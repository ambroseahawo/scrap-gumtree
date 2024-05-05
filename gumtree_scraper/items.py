# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Field, Item


class GumtreePropertiesItem(Item):
    # define the fields for your item here like:
    # Primary fields
    title = Field()
    location = Field()
    price = Field()
    image_urls = Field()
    description = Field()
    seller = Field()

    # Dynamic fields

    # Housekeeping fields
    url = Field()
    project = Field()
    spider = Field()
    server = Field()
    date = Field()
