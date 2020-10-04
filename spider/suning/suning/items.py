# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SuningItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    first_title = scrapy.Field()
    second_title = scrapy.Field()
    third_title = scrapy.Field()
    class_url = scrapy.Field()
    book_title = scrapy.Field()
    book_url = scrapy.Field()
    img_url = scrapy.Field()
    price = scrapy.Field()
    freight = scrapy.Field()
    seller = scrapy.Field()
