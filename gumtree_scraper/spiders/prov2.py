"""Scrapy spider for scraping property listings from Gumtree (flats/houses, UK)."""

import re
import socket
from datetime import datetime
from urllib.parse import urlparse, urlunparse

from itemloaders.processors import MapCompose, TakeFirst
from lxml import html
from scrapy import Request
from scrapy.item import Field
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider
from w3lib.html import remove_tags

from gumtree_scraper.items import GumtreePropertiesItem


class PropertiesSpider(CrawlSpider):
    """Crawls Gumtree listing pages, follows pagination, and extracts ad items."""

    name = "properties-v2"
    allowed_domains = ["gumtree.com"]
    start_urls = ["https://www.gumtree.com/flats-houses/uk/london"]

    rules = ()  # No rules; listing pages and pagination handled in parse_listing

    max_page = 50  # Stop after this page to avoid unbounded crawl

    item_link_extractor = LinkExtractor(restrict_xpaths='//article[@data-q="search-result"]//a')

    def start_requests(self):
        """Send start URLs to parse_listing so we never override CrawlSpider.parse."""
        for url in self.start_urls:
            yield Request(url, callback=self.parse_listing)

    def parse_listing(self, response):
        """Handle a listing page: yield item requests and the next page request."""
        for link in self.item_link_extractor.extract_links(response):
            yield Request(link.url, callback=self.parse_item)
        next_url = self.next_page_url(response.url)
        if next_url is not None:
            yield Request(next_url, callback=self.parse_listing)

    def next_page_url(self, url):
        """Build next listing page URL (e.g. .../london -> .../london/page2). Returns None if past max_page."""
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        match = re.search(r"/page(\d+)$", path)
        if match:
            page = int(match.group(1))
            if page >= self.max_page:
                return None
            next_path = path[: match.start()] + f"/page{page + 1}"
        else:
            next_path = path + "/page2"
        return urlunparse((parsed.scheme, parsed.netloc, next_path, "", parsed.query or "", parsed.fragment))

    def parse_item(self, response):
        """Extract a single property ad (title, price, location, description, attributes) into an item."""
        item_loader = ItemLoader(item=GumtreePropertiesItem(), response=response)
        # item_loader.default_output_processor = TakeFirst()

        item_loader.add_xpath("title", "//h1[1]/text()", MapCompose(str.strip, str.title))
        item_loader.add_xpath("location", '//h4[@data-q="ad-location"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("price", '//h3[@data-q="ad-price"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("image_urls", '//li[contains(@class,"carousel-item")]/img/@src')
        item_loader.add_xpath("description", '//p[@itemprop="description"]', MapCompose(remove_tags, self.format_paragraph))
        item_loader.add_xpath("seller", '//h2[@class="truncate-line seller-rating-block-name"]/text()', MapCompose(str.strip, str.title))

        attributes_container = response.xpath('//div[@data-q="attribute-container"]//dl').getall()
        for each_attribute in attributes_container:
            html_selector = html.fromstring(each_attribute)
            attribute_field = html_selector.xpath("//dt/text()")[0]
            attribute_value = html_selector.xpath("//dd/text()")[0]

            item_key = self.process_attr_str(attribute_field)
            GumtreePropertiesItem.fields[item_key] = Field(output_processor=TakeFirst())
            item_loader.add_value(item_key, attribute_value)

        # Housekeeping fields
        item_loader.add_value("url", response.url)
        item_loader.add_value("project", self.settings.get("BOT_NAME"))
        item_loader.add_value("spider", self.name)
        item_loader.add_value("server", socket.gethostname())
        item_loader.add_value("date", datetime.now().isoformat())
        # item_loader.add_value("date", datetime.now())
        # item_loader.add_value("date", datetime.now(timezone.utc)) timezone time

        return item_loader.load_item()

    def process_images_container(self, images_container):
        """Wrap a single images value in a list for the loader."""
        container = []
        container.append(images_container)
        return container

    def format_paragraph(self, job_description):
        """Normalize whitespace: collapse spaces and newlines to single spaces."""
        job_description = " ".join(job_description.split())

        # Replace newline characters with space
        job_description = job_description.replace("\n", " ")
        return job_description

    def process_attr_str(self, input_string):
        """Normalize attribute name to a lowercase, underscore-separated key."""
        input_string = input_string.strip()

        # Convert to lower case
        input_string = input_string.lower()

        input_string = "_".join(input_string.split())
        return input_string
