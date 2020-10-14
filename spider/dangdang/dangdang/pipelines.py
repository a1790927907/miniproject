# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import re
from pymongo import MongoClient
class DangdangPipeline:
    def open_spider(self,spider):
        self.mongo = MongoClient('localhost',27017)
        self.collection = self.mongo.dd.book

    def process_item(self, item, spider):
        item = self.deal_info(item)
        print(item)
        self.collection.insert(dict(item))
        return item

    def deal_info(self,item):
        item['book_title'] = re.sub(r'\n|\t|\r| ','',item['book_title'])
        return item

    def close_spider(self,spider):
        self.mongo.close()