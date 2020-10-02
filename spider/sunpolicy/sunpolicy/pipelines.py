# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from pymongo import MongoClient
mongo = MongoClient('localhost',27017)
collection = mongo.sun.suninfo

class SunpolicyPipeline:
    def process_item(self, item, spider):
        print(item)
        collection.insert(dict(item))
        return item
