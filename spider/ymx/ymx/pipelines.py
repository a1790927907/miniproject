# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

class YmxPipeline:
    def open_spider(self,spider):
        self.mongo = MongoClient('localhost',27017)
        self.collection = self.mongo.amazon.goods

    def process_item(self, item, spider):
        if spider.name == 'amazon':
            item = self.deal_info(item)
        print(item)
        # self.collection.insert(dict(item))
        return item

    def deal_info(self,item):
        item['goods_title'] = item['goods_title'].replace('\xa0','')
        return item

    def close_spider(self,spider):
        self.mongo.close()