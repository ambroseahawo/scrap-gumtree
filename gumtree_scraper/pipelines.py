# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# Modifying or storing Items—domain-specific, may be
# reused across projects.
# Write an Item Pipeline.
import json
import traceback
from datetime import datetime

import dj_database_url
import dj_redis_url
import psycopg2
import scrapy
import treq
import txredisapi

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
from twisted.internet import defer, reactor, task


class PostProcessItems(object):
    def process_item(self, item, spider):
        item["date"] = list(map(datetime.isoformat, item["date"]))
        return item


class GumtreeScraperPipeline:
    def process_item(self, item, spider):
        return item


class PostgresWriter(object):
    """
    A spider that writes to PostgreSQL databases
    """

    @classmethod
    def from_crawler(cls, crawler):
        """Retrieves scrapy crawler and accesses pipeline's settings"""

        # Get PostgreSQL URL from settings
        postgres_url = crawler.settings.get("POSTGRES_PIPELINE_URL", None)

        # If doesn't exist, disable the pipeline
        if not postgres_url:
            raise NotConfigured

        # Create the class
        return cls(postgres_url)

    def __init__(self, postgres_url):
        """Opens a PostgreSQL connection pool"""

        # Store the url for future reference
        self.postgres_url = postgres_url
        # Report connection error only once
        self.report_connection_error = True

        # Parse PostgreSQL URL and try to initialize a connection
        conn_kwargs = PostgresWriter.parse_postgres_url(postgres_url)
        self.dbpool = adbapi.ConnectionPool("psycopg2", connect_timeout=5, **conn_kwargs)

    def close_spider(self, spider):
        """Discard the database pool on spider close"""
        self.dbpool.close()

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """Processes the item. Does insert into PostgreSQL"""

        logger = spider.logger

        try:
            yield self.dbpool.runInteraction(self.do_replace, item)
        except psycopg2.OperationalError:
            if self.report_connection_error:
                logger.error("Can't connect to PostgreSQL: %s" % self.postgres_url)
                self.report_connection_error = False
        except:
            logger.exception("Database Error: ")
            # print(traceback.format_exc())

        # Return the item for the next stage
        defer.returnValue(item)

    @staticmethod
    def do_replace(tx, item):
        """Does the actual INSERT INTO"""

        sql = """INSERT INTO gumtree_properties (url, title, price, location)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (url) DO UPDATE SET
        title = EXCLUDED.title,
        price = EXCLUDED.price,
        location = EXCLUDED.location"""

        args = (item["url"], item["title"], item["price"], item["location"])

        tx.execute(sql, args)

    @staticmethod
    def parse_postgres_url(postgres_url):
        """
        Parses PostgreSQL url and prepares arguments for
        adbapi.ConnectionPool()
        """

        params = dj_database_url.parse(postgres_url)

        conn_kwargs = {}
        conn_kwargs["host"] = params["HOST"]
        conn_kwargs["user"] = params["USER"]
        conn_kwargs["password"] = params["PASSWORD"]
        conn_kwargs["database"] = params["NAME"]
        conn_kwargs["port"] = params["PORT"]

        # Remove items with empty values
        conn_kwargs = {k: v for k, v in conn_kwargs.items() if v}

        return conn_kwargs


class RedisCache(object):
    """A pipeline that uses a Redis server to cache values"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it Redis' url and namespace"""

        # Get redis URL
        redis_url = crawler.settings.get("REDIS_PIPELINE_URL", None)

        # If doesn't exist, disable
        if not redis_url:
            raise NotConfigured

        redis_nm = crawler.settings.get("REDIS_PIPELINE_NS", "ADDRESS_CACHE")

        return cls(crawler, redis_url, redis_nm)

    def __init__(self, crawler, redis_url, redis_nm):
        """Store configuration, open connection and register callback"""

        # Store the url and the namespace for future reference
        self.redis_url = redis_url
        self.redis_nm = redis_nm

        # Report connection error only once
        self.report_connection_error = True

        # Parse redis URL and try to initialize a connection
        args = RedisCache.parse_redis_url(redis_url)
        self.connection = txredisapi.lazyConnectionPool(connectTimeout=5, replyTimeout=5, **args)

        # Connect the item_scraped signal
        crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """Looks up address in redis"""

        logger = spider.logger

        if "location" in item:
            # Set by previous step (spider or pipeline). Don't do anything
            defer.returnValue(item)
            return

        # The item has to have the address field set
        assert ("address" in item) and (len(item["address"]) > 0)

        # Extract the address from the item.
        address = item["address"][0]

        try:
            # Check Redis
            key = self.redis_nm + ":" + address

            value = yield self.connection.get(key)

            if value:
                # Set the value for this item
                item["location"] = json.loads(value)

        except txredisapi.ConnectionError:
            if self.report_connection_error:
                logger.error("Can't connect to Redis: %s" % self.redis_url)
                self.report_connection_error = False

        defer.returnValue(item)

    def item_scraped(self, item, spider):
        """
        This function inspects the item after it has gone through every
        pipeline stage and if there is some cache value to add it does so.
        """
        # Capture and encode the location and the address
        try:
            location = item["location"]
            value = json.dumps(location, ensure_ascii=False)
        except KeyError:
            return

        # Extract the address from the item.
        address = item["address"][0]

        key = self.redis_nm + ":" + address

        quiet = lambda failure: failure.trap(txredisapi.ConnectionError)

        # Store it in Redis asynchronously
        return self.connection.set(key, value).addErrback(quiet)

    @staticmethod
    def parse_redis_url(redis_url):
        """
        Parses redis url and prepares arguments for
        txredisapi.lazyConnectionPool()
        """

        params = dj_redis_url.parse(redis_url)

        conn_kwargs = {}
        conn_kwargs["host"] = params["HOST"]
        conn_kwargs["password"] = params["PASSWORD"]
        conn_kwargs["dbid"] = params["DB"]
        conn_kwargs["port"] = params["PORT"]

        # Remove items with empty values
        conn_kwargs = {k: v for k, v in conn_kwargs.items() if v}

        return conn_kwargs


class CustomImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        image_urls_field = ItemAdapter(item).get("image_urls", None)
        if image_urls_field:
            image_urls = str(image_urls_field).split(",")
            for url in image_urls:
                yield scrapy.Request(url)


# custom image pipeline;-
# https://gist.github.com/farhadmpr/12ba6a3aa058138ec5c026a1a0f8eebd
# https://docs.scrapy.org/en/latest/topics/media-pipeline.html?highlight=image#:~:text=file%20is%20expired.-,Thumbnail%20generation%20for%20images,the%20values%20are%20their%20dimensions.
class Throttler(object):
    """
    A simple throttler helps you limit the number of requests you make
    to a limited resource
    """

    def __init__(self, rate):
        """It will callback at most ```rate``` enqueued things per second"""
        self.queue = []
        self.looping_call = task.LoopingCall(self._allow_one)
        self.looping_call.start(1.0 / float(rate))

    def stop(self):
        """Stop the throttler"""
        self.looping_call.stop()

    def throttle(self):
        """
        Call this function to get a deferred that will become available
        in some point in the future in accordance with the throttling rate
        """
        d = defer.Deferred()
        self.queue.append(d)
        return d

    def _allow_one(self):
        """Makes deferred callbacks periodically"""
        if self.queue:
            self.queue.pop(0).callback(None)


class DeferredCache(object):
    """
    A cache that always returns a value, an error or a deferred
    """

    def __init__(self, key_not_found_callback):
        """Takes as an argument"""
        self.records = {}
        self.deferreds_waiting = {}
        self.key_not_found_callback = key_not_found_callback

    @defer.inlineCallbacks
    def find(self, key):
        """
        This function either returns something directly from the cache or it
        calls ```key_not_found_callback``` to evaluate a value and return it.
        Uses deferreds to do this is a non-blocking manner.
        """
        # This is the deferred for this call
        rv = defer.Deferred()

        if key in self.deferreds_waiting:
            # We have other instances waiting for this key. Queue
            self.deferreds_waiting[key].append(rv)
        else:
            # We are the only guy waiting for this key right now.
            self.deferreds_waiting[key] = [rv]

            if not key in self.records:
                # If we don't have a value for this key we will evaluate it
                # using key_not_found_callback.
                try:
                    value = yield self.key_not_found_callback(key)

                    # If the evaluation succeeds then the action for this key
                    # is to call deferred's callback with value as an argument
                    # (using Python closures)
                    self.records[key] = lambda d: d.callback(value)
                except Exception as e:
                    # If the evaluation fails with an exception then the
                    # action for this key is to call deferred's errback with
                    # the exception as an argument (Python closures again)
                    self.records[key] = lambda d: d.errback(e)

            # At this point we have an action for this key in self.records
            action = self.records[key]

            # Note that due to ```yield key_not_found_callback```, many
            # deferreds might have been added in deferreds_waiting[key] in
            # the meanwhile
            # For each of the deferreds waiting for this key....
            for d in self.deferreds_waiting.pop(key):
                # ...perform the action later from the reactor thread
                reactor.callFromThread(action, d)

        value = yield rv
        defer.returnValue(value)


class GeoPipeline(object):
    """A pipeline that geocodes addresses using Google's API"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it crawler's stats object"""
        return cls(crawler.stats)

    def __init__(self, stats):
        """Initialize empty cache and stats object"""
        self.stats = stats
        self.cache = DeferredCache(self.cache_key_not_found_callback)
        self.throttler = Throttler(5)  # 5 Requests per second

    def close_spider(self, spider):
        """Stop the throttler"""
        self.throttler.stop()

    @defer.inlineCallbacks
    def geocode(self, address):
        """
        This method makes a call to Google's geocoding API. You shouldn't
        call this more than 5 times per second
        """

        # The url for this API
        # endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
        endpoint = "http://web:9312/maps/api/geocode/json"

        # Do the call
        parms = [("address", address), ("sensor", "false")]
        response = yield treq.get(endpoint, params=parms)

        # Decode the response as json
        content = yield response.json()

        # If the status isn't ok, return it as a string
        if content["status"] != "OK":
            raise Exception('Unexpected status="%s" for address="%s"' % (content["status"], address))

        # Extract the address and geo-point and set item's fields
        geo = content["results"][0]["geometry"]["location"]

        # Return the final value
        defer.returnValue({"lat": geo["lat"], "lon": geo["lng"]})

    @defer.inlineCallbacks
    def cache_key_not_found_callback(self, address):
        """
        This method makes an API call while respecting throttling limits.
        It also retries attempts that fail due to limits.
        """
        self.stats.inc_value("geo_pipeline/misses")

        while True:
            # Wait enough to adhere to throttling policies
            yield self.throttler.throttle()

            # Do the API call
            try:
                value = yield self.geocode(address)
                defer.returnValue(value)

                # Success
                break
            except Exception as e:
                if 'status="OVER_QUERY_LIMIT"' in str(e):
                    # Retry in this case
                    self.stats.inc_value("geo_pipeline/retries")
                    continue
                # Propagate the rest
                raise

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """
        Pipeline's main method. Uses inlineCallbacks to do
        asynchronous REST requests
        """

        if "location" in item:
            # Set by previous step (spider or pipeline). Don't do anything
            # apart from increasing stats
            self.stats.inc_value("geo_pipeline/already_set")
            defer.returnValue(item)
            return

        # The item has to have the address field set
        assert ("address" in item) and (len(item["address"]) > 0)

        # Extract the address from the item.
        try:
            item["location"] = yield self.cache.find(item["address"][0])
        except:
            self.stats.inc_value("geo_pipeline/errors")
            # print (traceback.format_exc())
            spider.logger.error(traceback.format_exc())

        # Return the item for the next stage
        defer.returnValue(item)
