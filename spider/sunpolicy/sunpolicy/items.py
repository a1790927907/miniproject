# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SunpolicyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    category = scrapy.Field()
    status = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    reponsetime = scrapy.Field()
    querytime = scrapy.Field()
    content = scrapy.Field()
    img_url_list = scrapy.Field()
