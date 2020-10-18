# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class YmxItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    first_title = scrapy.Field()
    second_title = scrapy.Field()
    goods_type = scrapy.Field()
    item_url = scrapy.Field()
    goods_title = scrapy.Field()
    upload_time = scrapy.Field()
    book_author = scrapy.Field()
    goods_shop = scrapy.Field()
    goods_img = scrapy.Field()
    goods_url = scrapy.Field()
    e_book_price = scrapy.Field()
    real_book_price = scrapy.Field()
    goods_price = scrapy.Field()
    freight = scrapy.Field()
    comments_good_rate = scrapy.Field()
    goods_price_type = scrapy.Field()
    book_desc = scrapy.Field()
    book_page = scrapy.Field()
