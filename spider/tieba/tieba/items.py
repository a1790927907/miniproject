# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TiebaItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    auther = scrapy.Field()
    detail_url = scrapy.Field()
    content = scrapy.Field()
    img_list = scrapy.Field()
    upload_time = scrapy.Field()
    is_top = scrapy.Field()
    article_id = scrapy.Field()

