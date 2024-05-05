from itemloaders.processors import MapCompose, TakeFirst
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
        Rule(
            LinkExtractor(restrict_xpaths='//a[@data-q="pagination-forward-page"]')
        ),  # //a[@data-q="pagination-forward-page"]/@href
        Rule(
            LinkExtractor(restrict_xpaths='//article[@data-q="search-result"]//a'), callback="parse_item"
        ),  # //a[@data-q="search-result-anchor"]/@href
    )

    def parse_item(self, response):
        item_loader = ItemLoader(item=GumtreePropertiesItem(), response=response)
        item_loader.default_output_processor = TakeFirst()

        item_loader.add_xpath("title", "//h1/text()", MapCompose(str.strip, str.title))
        item_loader.add_xpath("location", '//h4[@data-q="ad-location"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("price", '//h3[@data-q="ad-price"]/text()', MapCompose(str.strip))
        item_loader.add_xpath("images", '//li[contains(@class,"carousel-item")]/img/@src')
        item_loader.add_xpath(
            "description", '//p[@itemprop="description"]', MapCompose(remove_tags, self.format_paragraph)
        )

        return item_loader.load_item()

    def format_paragraph(self, job_description):
        # Replace multiple spaces with single space
        job_description = " ".join(job_description.split())

        # Replace newline characters with space
        job_description = job_description.replace("\n", " ")

        # Return formatted string
        return job_description
