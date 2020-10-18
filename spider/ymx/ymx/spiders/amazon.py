import scrapy
from scrapy_redis.spiders import RedisSpider
import re,json

from ymx.items import YmxItem
import copy
from urllib.parse import urljoin
class AmazonSpider(RedisSpider):
    name = 'amazon'
    allowed_domains = ['amazon.cn']
    base_url = 'https://www.amazon.cn/'
    redis_key = 'ymx'

    def parse(self, response):
        self.flag = 1
        #网页内是以一个Json来加载数据的
        #提取对应的Json
        all_data = re.findall(r'data\((.*?)</script>',response.text,re.S)[1]
        all_data = re.findall(r'(.*)\); }\);',all_data,re.S)[0]
        all_data = json.loads(all_data)
        #不必要的字段
        pop_list = ['signinContent','templates','cartContent','wishlistContent','yourAccountContent','DeepbrowseKindleReaderPanel','shopAllContent']
        #删除不必要字段
        for pop_key in pop_list:
            all_data.pop(pop_key)
        for data in all_data:
            item = YmxItem()
            try:
                all_t = all_data[data]['template']['data']['text1']
            except:
                all_t = 'ANOTHER'
            #电子书的处理方式与其他商品不同，需要区分
            if all_t == 'Kindle电子书':
                item['goods_type'] = 'book'
            else:
                item['goods_type'] = 'another'
            item_data = all_data[data]['template']['data']['items']
            for f_t in item_data:
                #获取一级标题
                item['first_title'] = f_t['text']
                item_st_data = f_t['items']
                for s_t in item_st_data:
                    #获取二级标题
                    item['second_title'] = s_t['text']
                    #由于存在超长url，所以这里先排除掉
                    if (len(s_t['url']) <= 1000) and s_t['text'] != '常见问题':
                        item['item_url'] = urljoin(self.base_url,s_t['url'])
                    else:
                        continue
                    #排除不必要的url
                    if '/b' in item['item_url']:
                        item_copy = copy.deepcopy(item)
                        yield scrapy.Request(item['item_url'],callback=self.parse_all_goods,meta={'item':item_copy})

    def parse_all_goods(self,response):
        item = copy.deepcopy(response.meta['item'])
        item_bak = copy.deepcopy(response.meta['item'])
        #获取所有商品
        all_goods_li = response.xpath('//li[contains(@id,"result_")]')
        #有些可能获取不到，所以这里需要区分
        if all_goods_li.extract_first() is not None:
            for goods_li in all_goods_li:
                item['goods_title'] = goods_li.xpath('.//h2[@data-attribute]/@data-attribute').extract_first()
                #图书类存入字段与其他类别的字段不同
                if item['goods_type'] == 'book':
                    #有些图书没有日期
                    if goods_li.xpath('.//a[contains(@class,"a-link-normal s-access-detail-page")]/following-sibling::span[@role="separator"]/text()') is not None:
                        item['upload_time'] = goods_li.xpath('.//a[contains(@class,"a-link-normal s-access-detail-page")]/following-sibling::span[@class="a-size-small a-color-secondary"][1]/text()')
                    else:
                        item['upload_time'] = 'UnKnown'
                    #作者可能存在多个
                    all_author = goods_li.xpath('.//div[@class="a-row a-spacing-small"]/div[2]/span/text()').extract()
                    try:
                        all_author.remove(None)
                    except:
                        pass
                    item['book_author'] = ''.join(all_author)
                else:
                    #商店可能存在多个，也可能没有商店
                    all_goods_shop = goods_li.xpath('.//div[@class="a-row a-spacing-mini"][1]/div[2]/span/text()').extract()
                    try:
                        all_goods_shop.remove(None)
                    except:
                        pass
                    item['goods_shop'] = ''.join(all_goods_shop)

                item['goods_img'] = goods_li.xpath('.//a[@class="a-link-normal a-text-normal"]/img/@src').extract_first()
                item['goods_url'] = goods_li.xpath('.//a[contains(@class,"a-link-normal s-access-detail-page")]/@href').extract_first()
                item_copy = copy.deepcopy(item)
                yield scrapy.Request(item['goods_url'],callback=self.parse_goods_detail,meta={'item':item_copy})
        else:
            #另一种商品元素
            all_goods_li = response.xpath('//div[@class="s-main-slot s-result-list s-search-results sg-row"]/div[@data-uuid]')
            if all_goods_li.extract_first() is None:
                return
            else:
                for goods_li in all_goods_li:
                    item['goods_title'] = goods_li.xpath('.//a[@class="a-link-normal a-text-normal"]/span/text()').extract_first()

                    if item['goods_type'] == 'book':
                        item['upload_time'] = goods_li.xpath('.//a[@class="a-link-normal a-text-normal"]/../../div/span[last()]/text()').extract_first()
                        all_book_author = goods_li.xpath('.//a[@class="a-link-normal a-text-normal"]/../../div/span[@class="a-size-base"]/text()').extract()
                        try:
                            all_book_author.remove(None)
                        except:
                            pass
                        item['book_author'] = ''.join(all_book_author)
                    #非图书直接返回
                    else:
                        return
                    item['goods_img'] = goods_li.xpath('.//img/@src').extract_first()
                    item['goods_url'] = urljoin(self.base_url,goods_li.xpath('.//a[@class="a-link-normal a-text-normal"]/@href').extract_first())
                    item_copy = copy.deepcopy(item)
                    yield scrapy.Request(item['goods_url'],callback=self.parse_goods_detail,meta={'item':item_copy})

        #翻页，有两种模式
        #如果都不存在，说明进了一个没有商品列表的url，或者到了最后一页的
        next_href_1 = response.xpath('//li[@class="a-last"]/a/@href').extract_first()
        next_href_2 = response.xpath('//a[@id="pagnNextLink"]/@href').extract_first()
        if next_href_1:
            next_page_url = urljoin(self.base_url,next_href_1)
            yield scrapy.Request(next_page_url,callback=self.parse_all_goods,meta={'item':item_bak})
        elif next_href_2:
            next_page_url = urljoin(self.base_url,next_href_2)
            yield scrapy.Request(next_page_url,callback=self.parse_all_goods,meta={'item':item_bak})

    def parse_goods_detail(self,response):
        item = copy.deepcopy(response.meta['item'])
        #图书分为电子书价格和实体书价格
        if item['goods_type'] == 'book':
            item['e_book_price'] = response.xpath('//span[@class="a-color-price"]/text()').extract_first()
            item['e_book_price'] = re.sub(r'\n|\t|\r| ','',re.findall(r'￥(.*)',item['e-book-price'],re.S)[0])
            item['real_book_price'] = response.xpath('//a[@class="a-size-mini a-link-normal"]/text()').extract_first()
            item['real_book_price'] = re.sub(r'\n|\t|\r| ','',re.findall(r'￥(.*)',item['real_book_price'],re.S)[0])
        else:
            #获取商品价格
            #秒杀价商品和普通商品的价格不同
            goods_price = response.xpath('//span[@id="priceblock_dealprice"]/text()').extract_first()
            if goods_price is not None:
                #秒杀商品
                item['goods_price_type'] = 'flash_scale'
                item['goods_price'] = re.sub(r'\n|\r|\t| |￥','',goods_price)
            else:
                #非秒杀商品
                item['goods_price_type'] = 'common_scale'
                goods_price = response.xpath('//span[@id="priceblock_ourprice"]/text()').extract_first()
                item['goods_price'] = re.sub(r'\n|\r|\t| |￥', '', goods_price)
            #获取运费
            freight = response.xpath('//div[@id="olp-new"]//span[@class="a-size-base"]/text()').extract_first()

            if freight is not None:
                item['freight'] = re.sub(r'\n|\t|\r| |￥','',freight)
            else:
                #部分为vip免运费
                item['freight'] = 'vip 0'

        good_rate = response.xpath('//span[@id="acrPopover"]/@title').extract_first()
        if good_rate is not None:
            item['comments_good_rate'] = good_rate
        else:
            #部分没有评价
            item['comments_good_rate'] = '0.0颗'
        item['comments_good_rate'] = float(re.findall(r'(.*?)颗',item['comments_good_rate'].replace(' ',''))[0])
        yield item




