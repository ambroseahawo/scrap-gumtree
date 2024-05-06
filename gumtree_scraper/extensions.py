import logging
from time import time

from scrapy import signals
from scrapy.exceptions import NotConfigured
from twisted.internet import task

logger = logging.getLogger(__name__)


class SetLoggingFileTerminal:
    @classmethod
    def from_crawler(cls, crawler):
        # settings = crawler.settings
        # enable logging on both log_file and terminal
        logging.basicConfig(
            level=logging.DEBUG, format="[%(asctime)s] %(name)s %(levelname)s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        # logger = logging.getLogger(__name__)
        logging.getLogger().addHandler(logging.StreamHandler())

        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler


class TrackItemsScraped:
    def __init__(self, item_count):
        self.item_count = item_count
        self.items_scraped = 0

    @classmethod
    def from_crawler(cls, crawler):
        # first check if the extension should be enabled and raise
        # NotConfigured otherwise
        if not crawler.settings.getbool("MYEXT_ENABLED"):
            raise NotConfigured

        # get the number of items from settings
        item_count = crawler.settings.getint("MYEXT_ITEMCOUNT", 100)

        # instantiate the extension object
        ext = cls(item_count)

        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)

        # return the extension object
        return ext

    def spider_opened(self, spider):
        # logger.info("opened spider %s", spider.name)
        pass

    def spider_closed(self, spider):
        # logger.info("closed spider %s", spider.name)
        pass

    def item_scraped(self, item, spider):
        self.items_scraped += 1
        if self.items_scraped % self.item_count == 0:
            logger.info("Scraped %d items", self.items_scraped)


class Latencies:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler
        self.interval = crawler.settings.getfloat("LATENCIES_INTERVAL")
        if not self.interval:
            raise NotConfigured

        cs = crawler.signals
        cs.connect(self._spider_opened, signal=signals.spider_opened)
        cs.connect(self._spider_closed, signal=signals.spider_closed)
        cs.connect(self._request_scheduled, signal=signals.request_scheduled)
        cs.connect(self._response_received, signal=signals.response_received)
        cs.connect(self._item_scraped, signal=signals.item_scraped)
        cs.connect(self._item_dropped, signal=signals.item_dropped)

        self.latency, self.proc_latency, self.items = 0, 0, 0

    def _spider_opened(self, spider):
        self.task = task.LoopingCall(self._log, spider)
        self.task.start(self.interval)

    def _spider_closed(self, spider, reason):
        if hasattr(self, "task") and self.task.running:
            self.task.stop()

    def _request_scheduled(self, request, spider):
        request.meta["schedule_time"] = time()

    def _response_received(self, response, request, spider):
        request.meta["received_time"] = time()

    def _item_scraped(self, item, response, spider):
        self.latency += time() - response.meta["schedule_time"]
        self.proc_latency += time() - response.meta["received_time"]
        self.items += 1

    def _item_dropped(self, item, response, exception, spider):
        stats = spider.crawler.stats.get_stats()
        try:
            item_count = int(stats["item_scraped_count"])
            if item_count:
                item_count -= 1
        except:
            pass

    def _log(self, spider):
        irate = float(self.items) / self.interval
        latency = self.latency / self.items if self.items else 0
        proc_latency = self.proc_latency / self.items if self.items else 0
        spider.logger.info(
            ("Scraped %d items at %.1f items/s, avg latency: " "%.2f s and avg time in pipelines: %.2f s")
            % (self.items, irate, latency, proc_latency)
        )
        self.latency, self.proc_latency, self.items = 0, 0, 0
