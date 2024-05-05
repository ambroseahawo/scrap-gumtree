from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from scrapy.spiders import CrawlSpider, Rule


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
            LinkExtractor(restrict_xpaths='//a[@data-q="search-result-anchor"]'), callback="parse_item"
        ),  # //a[@data-q="search-result-anchor"]/@href
    )

    # def parse(self, response):
    #     # title, location, price, images, description
    #     title = response.xpath("//h1/text()").get()
    #     location = response.xpath('//h4[@data-q="ad-location"]/text()').get()
    #     price = response.xpath('//h3[@data-q="ad-price"]/text()').get()
    #     images = response.xpath('//li[contains(@class,"carousel-item")]/img/@src').get()
    #     description = response.xpath('//p[@itemprop="description"]').get()

    #     data = {"title": title, "location": location, "price": price, "images": images, "description": description}

    #     self.log(data)

    def parse_item(self, response):
        item = {}
        # item["domain_id"] = response.xpath('//input[@id="sid"]/@value').get()
        # item["name"] = response.xpath('//div[@id="name"]').get()
        # item["description"] = response.xpath('//div[@id="description"]').get()
        return item
