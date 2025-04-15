# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
import logging

import scrapy
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.pipelines.files import FilesPipeline

logger = logging.getLogger(__name__)
from scrapy import Request



class RealestateScrapyPipeline:
    def process_item(self, item, spider):
        return item


