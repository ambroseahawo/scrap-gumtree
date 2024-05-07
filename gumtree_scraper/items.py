# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from itemloaders.processors import TakeFirst
from scrapy.item import Field, Item


class GumtreePropertiesItem(Item):
    # define the fields for your item here like:
    # Primary fields
    title = Field(output_processor=TakeFirst())
    location = Field(output_processor=TakeFirst())
    price = Field(output_processor=TakeFirst())
    description = Field(output_processor=TakeFirst())
    seller = Field(output_processor=TakeFirst())
    posted = Field(output_processor=TakeFirst())
    image_urls = Field()
    images = Field()

    # Dynamic fields
    # property_type = Field(output_processor=TakeFirst())
    # seller_type = Field(output_processor=TakeFirst())
    # number_of_bedrooms = Field(output_processor=TakeFirst())
    # date_available = Field(output_processor=TakeFirst())

    # Housekeeping fields
    url = Field(output_processor=TakeFirst())
    project = Field(output_processor=TakeFirst())
    spider = Field(output_processor=TakeFirst())
    server = Field(output_processor=TakeFirst())
    date = Field(output_processor=TakeFirst())
