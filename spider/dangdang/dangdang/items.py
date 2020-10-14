# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DangdangItem(scrapy.Item):
    # define the fields for your item here like:
    first_title = scrapy.Field()
    second_title = scrapy.Field()
    third_title = scrapy.Field()
    label_url = scrapy.Field()
    book_sku_id = scrapy.Field()
    book_title = scrapy.Field()
    book_img = scrapy.Field()
    create_time = scrapy.Field()
    book_publisher = scrapy.Field()
    book_publisher_url = scrapy.Field()
    book_url = scrapy.Field()
    book_comments_count = scrapy.Field()
    book_price = scrapy.Field()
    stock_status = scrapy.Field()
    book_type = scrapy.Field()
    good_counts = scrapy.Field()
    poor_counts = scrapy.Field()
    good_rate = scrapy.Field()


