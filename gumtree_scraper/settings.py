# Scrapy settings for gumtree_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime

from helpers import setup_project_folders

BOT_NAME = "gumtree_scraper"

SPIDER_MODULES = ["gumtree_scraper.spiders"]
NEWSPIDER_MODULE = "gumtree_scraper.spiders"

LOGS_FOLDER_NAME = "logs"
ITEMS_FOLDER_NAME = "items"

setup_project_folders(LOGS_FOLDER_NAME, ITEMS_FOLDER_NAME)

LOG_ENABLED = True
LOG_FILE = "{0}/{1}_{2}.log".format(LOGS_FOLDER_NAME, BOT_NAME, datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S"))
LOG_LEVEL = "DEBUG"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = "gumtree_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "gumtree_scraper.middlewares.GumtreeScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "gumtree_scraper.middlewares.GumtreeScraperDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
    "gumtree_scraper.extensions.SetLoggingFileTerminal": 100,
    "gumtree_scraper.extensions.Latencies": 200,
    # "gumtree_scraper.extensions.TrackItemsScraped": 300,
}

MYEXT_ENABLED = True
MYEXT_ITEMCOUNT = 10
LATENCIES_INTERVAL = 5.0

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "scrapy.pipelines.images.ImagesPipeline": 1,
    # "gumtree_scraper.pipelines.PostTidyItems": 100,
    "gumtree_scraper.pipelines.GumtreeScraperPipeline": 300,
}

IMAGES_STORE = "images"
IMAGES_THUMBS = {"small": (30, 30)}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
