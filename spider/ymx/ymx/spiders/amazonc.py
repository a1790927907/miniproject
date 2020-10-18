import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from scrapy_redis.spiders import RedisCrawlSpider
from ymx.items import YmxItem
import re
from urllib.parse import unquote
from html import unescape

'''
并发过多会出现验证码验证，需要间隔访问并且少并发
个人不倾向于使用crawlspider
'''
class AmazoncSpider(RedisCrawlSpider):
    name = 'amazonc'
    allowed_domains = ['amazon.cn']
    #https://www.amazon.cn/Kindle%E7%94%B5%E5%AD%90%E4%B9%A6/b/460-8117751-8908848?ie=UTF8&node=116169071&ref_=sa_menu_top_ebook
    redis_key = 'amazon:start_url'

    rules = (
        Rule(LinkExtractor(restrict_xpaths=('//div[@id="contentGrid_732724"]/div/div[position()>1]//a',)), follow=True),

        # 翻页
        # 到第3页开始出现变化
        Rule(LinkExtractor(restrict_xpaths=('//li[contains(@id,"result_")]//div[@class="a-column a-span12 a-text-center"]/a',)),callback='parse_item'),

        #变化后翻页
        Rule(LinkExtractor(restrict_xpaths=('//span[@class="a-size-medium a-color-base a-text-normal"]/..',)),callback='parse_item'),

        #同理变化
        Rule(LinkExtractor(restrict_xpaths=('//span[@id="pagnNextString"]/..',)),follow=True),

        Rule(LinkExtractor(restrict_xpaths=('//li[@class="a-last"]/a',)), follow=True),
    )

    def parse_item(self, response):
        item = YmxItem()
        item['goods_title'] = response.xpath('//span[@id="productTitle"]/text()').extract_first()
        item['e_book_price'] = float(re.sub(r'\n|\t|\r| |￥','',response.xpath('//span[@class="a-color-base"]/span/text()').extract_first()))
        item['first_title'] = re.sub(r'\t|\n|\r| ','',response.xpath('//ul[@class="a-unordered-list a-horizontal a-size-small"]/li[last()]//a/text()').extract_first())
        item['goods_url'] = response.url
        all_author = response.xpath('//span[@class="author notFaded"]')
        authors = [re.sub(r'\n|\t|\r| ','',i.xpath('string(.)').extract_first()) for i in all_author]
        item['book_author'] = ''.join(authors)
        item['book_page'] = response.xpath('//span[contains(@data-a-popover,"页数")]/a[@class="a-popover-trigger a-declarative"]/text()').extract_first()
        try:
            item['book_page'] = int(re.findall(r'共(.*?)页',item['book_page'],re.S)[0])
        except:
            pass
        #出版社的li标签不确定
        goods_shop_li = response.xpath('//div[@id="detailBullets_feature_div"]/ul/li/span/span[1]')
        for li in goods_shop_li:
            if '出版社' in li.xpath('./text()').extract_first():
                item['goods_shop'] = li.xpath('./../span[2]/text()').extract_first()
                break
        else:
            item['goods_shop'] = None
        #描述被html编码了
        all_desc = re.findall(r'bookDescEncodedData.*?=.*?"(.*?)"',response.text,re.S)[0]
        desc = unescape(unquote(all_desc))
        item['book_desc'] = re.sub(r'<.*?>','',desc.replace('<br />','\n')).replace('手机下载Kindle APP，领取新人专享福利','').replace('\n','',1).replace(' ','',1)
        item['comments_good_rate'] = response.xpath('//div[@class="a-row"]/span[@class="a-size-base a-nowrap"]/span/text()').extract_first()
        if item['comments_good_rate'] is not None:
            item['comments_good_rate'] = float(re.findall(r'(.*?)，',item['comments_good_rate'])[0])
        else:
            item['comments_good_rate'] = 0.0
        item['goods_img'] = response.xpath('//div[@id="ebooks-img-canvas"]/img/@src').extract_first()
        yield item

