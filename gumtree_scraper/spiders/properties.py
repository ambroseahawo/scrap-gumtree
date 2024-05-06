import socket
from datetime import datetime, timezone

from itemloaders.processors import MapCompose, TakeFirst
from lxml import html
from scrapy.item import Field
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider, Rule
from w3lib.html import remove_tags

from gumtree_scraper.items import GumtreePropertiesItem


class PropertiesSpider(CrawlSpider):
    name = "properties"
    allowed_domains = ["gumtree.com"]
    start_urls = ["https://www.gumtree.com/flats-houses/uk/london"]

    # rules = (Rule(LinkExtractor(allow=r"Items/"), callback="parse_item", follow=True),)
    rules = (
        # Rule(
        #     LinkExtractor(restrict_xpaths='//a[@data-q="pagination-forward-page"]')
        # ),  # //a[@data-q="pagination-forward-page"]/@href
        Rule(
            LinkExtractor(restrict_xpaths='//article[@data-q="search-result"]//a'), callback="parse_item"
        ),  # //a[@data-q="search-result-anchor"]/@href
    )

    def parse_item(self, response):
        item_loader = ItemLoader(item=GumtreePropertiesItem(), response=response)
        # item_loader.default_output_processor = TakeFirst()

        item_loader.add_xpath("title", "//h1/text()", MapCompose(str.strip, str.title))
        item_loader.add_xpath("location", '//h4[@data-q="ad-location"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("price", '//h3[@data-q="ad-price"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("image_urls", '//li[contains(@class,"carousel-item")]/img/@src')
        item_loader.add_xpath(
            "description", '//p[@itemprop="description"]', MapCompose(remove_tags, self.format_paragraph)
        )
        item_loader.add_xpath(
            "seller", '//h2[@class="truncate-line seller-rating-block-name"]/text()', MapCompose(str.strip, str.title)
        )

        attributes_container = response.xpath('//div[@data-q="attribute-container"]//dl').getall()
        for each_attribute in attributes_container:
            html_selector = html.fromstring(each_attribute)
            attribute_field = html_selector.xpath("//dt/text()")[0]
            attribute_value = html_selector.xpath("//dd/text()")[0]

            item_key = self.process_attr_str(attribute_field)
            GumtreePropertiesItem.fields[item_key] = Field()
            item_loader.add_value(item_key, attribute_value)

        # Housekeeping fields
        item_loader.add_value("url", response.url)
        item_loader.add_value("project", self.settings.get("BOT_NAME"))
        item_loader.add_value("spider", self.name)
        item_loader.add_value("server", socket.gethostname())
        item_loader.add_value("date", datetime.now())
        # item_loader.add_value("date", datetime.now(timezone.utc)) timezone time

        return item_loader.load_item()

    def process_images_container(self, images_container):
        # return ",".join(images_container)
        container = []
        container.append(images_container)
        return container

    def format_paragraph(self, job_description):
        # Replace multiple spaces with single space
        job_description = " ".join(job_description.split())

        # Replace newline characters with space
        job_description = job_description.replace("\n", " ")

        # Return formatted string
        return job_description

    def process_attr_str(self, input_string):
        # Remove whitespaces
        input_string = input_string.strip()

        # Convert to lower case
        input_string = input_string.lower()

        # Join words with underscore
        input_string = "_".join(input_string.split())

        # Remove non-alphanumeric characters
        # input_string = "".join(char for char in input_string if char.isalnum())

        return input_string
