# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# Modifying or storing Items—domain-specific, may be
# reused across projects.
# Write an Item Pipeline.

import traceback
from datetime import datetime

import dj_database_url
import psycopg2
import scrapy

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import NotConfigured
from scrapy.pipelines.images import ImagesPipeline
from twisted.enterprise import adbapi
from twisted.internet import defer


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
