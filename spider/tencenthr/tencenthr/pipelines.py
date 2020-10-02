# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import logging
mongo = MongoClient('localhost',27017)
logger = logging.getLogger(__name__)

collection = mongo.hr.hrinfo3
class TencenthrPipeline:
    def process_item(self, item, spider):
        print(item)
        collection.insert(item)
        try:
            logger.warning(f'成功存储f{item["category_name"]} -- {item["job_name"]}')
        except:
            logger.warning('当前数据存储失败')
        return item
