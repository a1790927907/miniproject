# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient


class SuningPipeline:
    def open_spider(self,spider):
        mongo = MongoClient('localhost',27017)
        collection = mongo.suning.book
        self.collection = collection
        self.mongo = mongo


    def process_item(self, item, spider):
        item['book_title'] = self.process_title(item['book_title'])
        print(item)
        # self.collection.insert(dict(item))
        return item

    def process_title(self,title):
        return title.replace('\n','').replace('\t','').strip()

    def close_spider(self,spider):
        self.mongo.close()

