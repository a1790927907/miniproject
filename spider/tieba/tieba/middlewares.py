# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
import random

class TiebaDownloaderMiddleware:

    def process_request(self, request, spider):
        request.headers['User-Agent'] = random.choice(spider.settings['UA_LIST'])
