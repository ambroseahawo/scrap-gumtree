# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import hashlib

import scrapy

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes


class GumtreeScraperPipeline:
    def process_item(self, item, spider):
        return item


class CustomImagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        image_urls_field = ItemAdapter(item).get("image_urls", None)
        if image_urls_field:
            image_urls = str(image_urls_field).split(",")
            for url in image_urls:
                yield scrapy.Request(url)


# custom image pipeline;- https://gist.github.com/farhadmpr/12ba6a3aa058138ec5c026a1a0f8eebd
