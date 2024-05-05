# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Field, Item


class GumtreeScraperItem(Item):
    # define the fields for your item here like:
    title = Field()
    location = Field()
    price = Field()
    images = Field()
    description = Field()
