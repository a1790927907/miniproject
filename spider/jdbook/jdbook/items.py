# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JdbookItem(scrapy.Item):
    # define the fields for your item here like:
    first_title = scrapy.Field()
    second_title = scrapy.Field()
    third_title = scrapy.Field()
    link_url = scrapy.Field()
    book_name = scrapy.Field()
    book_url = scrapy.Field()
    img_url = scrapy.Field()
    shop_name = scrapy.Field()
    shop_url = scrapy.Field()
    price = scrapy.Field()
    e_book_price = scrapy.Field()
    comment_count = scrapy.Field()
    good_count = scrapy.Field()
    good_rate = scrapy.Field()
    poor_count = scrapy.Field()
    stock_state = scrapy.Field()
