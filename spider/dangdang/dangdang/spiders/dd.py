import scrapy
from dangdang.items import DangdangItem
import re
import copy
from urllib.parse import urljoin
import random

class DdSpider(scrapy.Spider):
    name = 'dd'
    allowed_domains = ['book.dangdang.com','product.dangdang.com','search.dangdang.com','category.dangdang.com','e.dangdang.com']
    start_urls = ['http://book.dangdang.com/']

    def parse(self, response):
        all_data_x = response.xpath('//div[@class="con flq_body"]')[0]
        all_first_title = all_data_x.xpath('./div[contains(@class,"level_one")]')
        for first_title_e in all_first_title:
            f = first_title_e.xpath('./dl/dt/text()').extract_first()
            if f is not None:
                item = DangdangItem()
                f = re.sub(r'\r|\n|\t| ','',f)
                if not f:
                    f = first_title_e.xpath('./dl/dt/a/text()').extract()
                    f = ''.join(f)
                    f = re.sub(r'\r|\n|\t| ','',f)
                item['first_title'] = f
                all_s_t_title = first_title_e.xpath('.//div[@class="col eject_left"]/dl')
                if all_s_t_title.extract_first() is not None:
                    for s_t in all_s_t_title:
                        second_title = s_t.xpath('./dt/text()').extract_first()
                        second_title = re.sub(r'\r|\n|\t| ','',second_title)
                        if second_title:
                            item['second_title'] = second_title
                        else:
                            item['second_title'] = s_t.xpath('./dt/a/text()').extract_first()
                        item['second_title'] = item['second_title'].replace(' ','')
                        all_third_title = s_t.xpath('./dd/a')
                        for third_e in all_third_title:
                            item['third_title'] = third_e.xpath('./@title').extract_first()
                            item['label_url'] = third_e.xpath('./@href').extract_first()
                            if ('search.dangdang.com' in item['label_url']) or ('category.dangdang.com' in item['label_url']):
                                item_copy = copy.deepcopy(item)
                                yield scrapy.Request(item_copy['label_url'],callback=self.parse_book_detail,meta={'item':item_copy})

    def parse_book_detail(self,response):
        item = copy.deepcopy(response.meta['item'])
        item_bak = copy.deepcopy(response.meta['item'])
        all_book = response.xpath('//ul[@class="bigimg"]/li')
        for book_li in all_book:
            item['book_sku_id'] = book_li.xpath('./@id').extract_first().replace('p','')
            item['book_title'] = book_li.xpath('./p[@class="name"]/a/@title').extract_first()
            book_img = book_li.xpath('./a/img/@data-original').extract_first()
            if book_img is not None:
                item['book_img'] = book_img
            else:
                item['book_img'] = book_li.xpath('./a/img/@src').extract_first()
            item['create_time'] = book_li.xpath('./p[@class="search_book_author"]/span[2]/text()').extract_first()
            if item['create_time'] is not None:
                item['create_time'] = item['create_time'].replace('/','').replace(' ','')
            item['book_publisher'] = book_li.xpath('./p[@class="search_book_author"]/span[3]/a/@title').extract_first()
            item['book_publisher_url'] = book_li.xpath('./p[@class="search_book_author"]/span[3]/a/@href').extract_first()
            item['book_url'] = book_li.xpath('./p[@class="name"]/a/@href').extract_first()
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(item['book_url'],callback=self.parse_book_price_comment,meta={'item':item_copy})
        next_page_url = response.xpath('//li[@class="next"]/a/@href').extract_first()
        if next_page_url:
            next_page_url = urljoin(response.url, next_page_url)
            yield scrapy.Request(next_page_url,callback=self.parse_book_detail,meta={'item':item_bak})

    def parse_book_price_comment(self,response):
        item = copy.deepcopy(response.meta['item'])
        headers = {
            'User-Agent': random.choice(self.settings['UA_LIST']),
            'X-Requested-With': 'XMLHttpRequest'
        }
        if 'e.dangdang.com' in response.url:
            e_book_url = 'http://e.dangdang.com/media/api.go?action=getMedia&deviceSerialNo=html5&macAddr=html5&channelType=html5&permanentId=&returnType=json&channelId=70000&clientVersionNo=6.8.0&platformSource=DDDS-P&fromPlatform=106&deviceType=pconline&token=&refAction=browse&saleId='+item['book_sku_id']+'&promotionType=1'
            item['book_type'] = 'e-book'
            item['book_comments_count'] = int(response.css('.count_per>em:nth-child(1)::text').extract_first().replace('人评论',''))
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(e_book_url,callback=self.parse_e_book_all_info,meta={'item':item_copy})
        else:
            cate_path = re.findall(r'"categoryPath":"(.*?)"',response.text)[0]
            item['book_type'] = 'real-book'
            item['book_comments_count'] = int(response.css('#comm_num_down::text').extract_first())
            item_copy = copy.deepcopy(item)
            info_url = 'http://product.dangdang.com/index.php?r=callback%2Fproduct-info&productId=' + item['book_sku_id'] + '&isCatalog=0&shopId=0&productType=0'
            yield scrapy.Request(info_url,callback=self.parse_book_all_info,headers=headers,meta={'item':item_copy,'cate_path':cate_path})

    def parse_book_all_info(self,response):
        item = copy.deepcopy(response.meta['item'])
        cate_path = response.meta['cate_path']
        data = response.json()['data']
        item['book_price'] = data['spu']['price']['salePrice']
        item['stock_status'] = int(data['spu']['stock']['stockStatus'])
        item_copy = copy.deepcopy(item)
        comment_url = 'http://product.dangdang.com/index.php?r=comment%2Flist&productId='+item['book_sku_id']+'&categoryPath='+cate_path+'&mainProductId='+item['book_sku_id']+'&mediumId=0&pageIndex=1&sortType=1&filterType=1&isSystem=1&tagId=0&tagFilterCount=0&template=publish'
        yield scrapy.Request(comment_url,callback=self.parse_book_comment_count,meta={'item':item_copy})

    def parse_e_book_all_info(self,response):
        item = copy.deepcopy(response.meta['item'])
        all_data = response.json()
        item['book_price'] = all_data['data']['mediaSale']['mediaList'][0]['salePrice']
        item['stock_status'] = 1
        item['good_counts'] = 0
        item['poor_counts'] = 0
        item['good_rate'] = 0
        yield item

    def parse_book_comment_count(self,response):
        item = copy.deepcopy(response.meta['item'])
        all_data = response.json()
        item['good_counts'] = all_data['data']['list']['summary']['total_crazy_count']
        item['poor_counts'] = all_data['data']['list']['summary']['total_detest_count']
        item['good_rate'] = all_data['data']['list']['summary']['goodRate']
        yield item




