# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

# Modifying or storing Items—domain-specific, may be
# reused across projects.
# Write an Item Pipeline.

from datetime import datetime

import scrapy

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline


class PostTidyItems(object):
    def process_item(self, item, spider):
        item["date"] = list(map(datetime.isoformat, item["date"]))
        return item


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


# custom image pipeline;-
# https://gist.github.com/farhadmpr/12ba6a3aa058138ec5c026a1a0f8eebd
# https://docs.scrapy.org/en/latest/topics/media-pipeline.html?highlight=image#:~:text=file%20is%20expired.-,Thumbnail%20generation%20for%20images,the%20values%20are%20their%20dimensions.
