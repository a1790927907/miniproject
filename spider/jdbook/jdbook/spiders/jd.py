import scrapy
from jdbook.items import JdbookItem
import copy
import execjs
from urllib.parse import quote
import random
import re
import logging
logger = logging.getLogger(__name__)

class JdSpider(scrapy.Spider):
    name = 'jd'
    allowed_domains = ['book.jd.com','list.jd.com','search.jd.com','lapi.jd.com','item.jd.com','c.3.cn','club.jd.com','c0.3.cn']
    start_urls = ['https://lapi.jd.com/pool?body={%22pid%22:%220101947%22}&source=book']

    def parse(self, response):
        all_data = response.json()
        for data in all_data['data']:
            item = JdbookItem()
            headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
            #获取一级标题
            item['first_title'] = data['title']
            #获取一级标题的id
            pool_id = data['ext_info']['poolId']
            _ = execjs.eval('new Date().getTime()')
            item_copy = copy.deepcopy(item)
            body_param = quote('"pid":"'+ str(pool_id) +'"').replace('%3A',':')
            url = 'https://lapi.jd.com/pool?body={' + body_param + '}&source=book&_=' + str(_)
            yield scrapy.Request(url,callback=self.parse_title,headers=headers,meta={'item':item_copy})

    def parse_title(self,response):
        item = response.meta['item']
        try:
            all_data = response.json()
        except:
            logger.warning(f'url: {response.url} 获取标题失败')
            return
        for data in all_data['data']:
            #获取二级标题
            item['second_title'] = data['title']
            for third_data in data['children']:
                headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
                #获取三级标题
                item['third_title'] = third_data['title']
                item['link_url'] = third_data['link_value']
                item_copy = copy.deepcopy(item)
                #不同url使用不同回调函数
                if (self.allowed_domains[0] + '/booktop') in item['link_url']:
                    yield scrapy.Request(item['link_url'], callback=self.parse_book_name_book_jd,headers=headers,meta={'item': item_copy})
                elif self.allowed_domains[1] in item['link_url']:
                    yield scrapy.Request(item['link_url'],callback=self.parse_book_name_list_jd,headers=headers,meta={'item':item_copy})
                elif self.allowed_domains[2] in item['link_url']:
                    yield scrapy.Request(item['link_url'], callback=self.parse_book_name_search_jd,headers=headers,meta={'item': item_copy})
                elif self.allowed_domains[4] in item['link_url']:
                    yield scrapy.Request(item['link_url'],callback=self.parse_book_in_item_page,headers=headers,meta={'item':item_copy})

    def parse_book_in_item_page(self,response):
        #部分直接进入item页面的url
        item = copy.deepcopy(response.meta['item'])
        headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
        item['book_name'] = response.xpath('//div[@class="sku-name"]/text()').extract_first()
        item['book_url'] = response.url
        item['img_url'] = 'http:' + response.xpath('//div[@id="spec-n1"]/img/@data-origin').extract_first()
        item['shop_name'] = response.xpath('//span[@class="shop-name"]/text()').extract_first()
        item['shop_url'] = 'https:' + response.xpath('//div[@class="J-hove-wrap EDropdown fr"]/div[@class="item"]/div[@class="name"]/a/@href').extract_first()
        item_copy = copy.deepcopy(item)
        yield scrapy.Request(response.url,callback=self.parse_price_info,headers=headers,meta={'item':item_copy})

    def parse_book_name_list_jd(self,response):
        #此url下book的信息在另一个url下
        item = copy.deepcopy(response.meta['item'])
        #先看看cat在不在url里，如果在的话，不管tid
        if 'cat' in response.url:
            params = 'cat=' + quote(re.findall(r'cat=(.*?)&',response.url+'&')[0])
        elif 'tid' in response.url:
            params = 'tid=' + re.findall(r'tid=(.*?)&',response.url+'&')[0]
        advware_count = int(re.findall(r's.init\(.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?\)', response.text, re.S)[0].replace(' ', ''))
        log_id = re.findall(r"log_id:'(.*?)'",response.text)[0]
        page_count = int(re.findall(r'page_count:"(.*?)"',response.text)[0])
        for page in range(page_count):
            headers = {'user-agent': random.choice(self.settings['UA_LIST']),'referer': 'https://list.jd.com/list.html'}
            if advware_count > 0:
                s = page * (30 - advware_count) + 1
            else:
                s = page * 30 + 1
            url = 'https://list.jd.com/listNew.php?' + params + '&page=' + str(page + 1) + '&s=' + str(s) +'&scrolling=y&log_id=' + log_id + '&tpl=2_M&isList=1'
            yield scrapy.Request(url,callback=self.parse_detail,headers=headers,meta={'item':item})

    def parse_book_name_search_jd(self,response):
        #此url下大部分和list.jd.com一样，但是图书的具体信息是不一样的url
        item = copy.deepcopy(response.meta['item'])
        params = re.findall(r'Search\?(.*)',response.url,re.I)[0]
        advware_count = int(re.findall(r's.init\(.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,(.*?),.*?\)',response.text, re.S)[0].replace(' ', ''))
        log_id = re.findall(r"log_id:'(.*?)'", response.text)[0]
        page_count = int(re.findall(r'page_count:"(.*?)"', response.text)[0])
        for page in range(page_count):
            headers = {'user-agent': random.choice(self.settings['UA_LIST']),
                       'referer': 'https://search.jd.com/Search'}
            if advware_count > 0:
                s = page * (30 - advware_count) + 1
            else:
                s = page * 30 + 1
            url = 'https://search.jd.com/s_new.php?'+ params +'&page='+ str(page + 1) +'&s='+str(s)+'&scrolling=y&log_id=' + log_id + '&tpl=2_M&isList=1'
            yield scrapy.Request(url, callback=self.parse_detail, headers=headers, meta={'item': item})


    def parse_book_name_book_jd(self,response):
        # 此url下book的信息能直接获得
        item = copy.deepcopy(response.meta['item'])
        item_bak = copy.deepcopy(response.meta['item'])
        all_info = response.xpath('//div[@class="mc"]//ul/li')
        for info in all_info:
            headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
            item['book_name'] = info.xpath('./div[@class="p-detail"]/a/text()').extract_first()
            item['book_url'] = 'https:' + info.xpath('./div[@class="p-detail"]/a/@href').extract_first()
            item['img_url'] = 'http:' + info.xpath('./div[@class="p-img"]/a/img/@src').extract_first()
            item['shop_name'] = info.xpath('div[@class="p-detail"]/dl[2]/dd/a/text()').extract_first()
            item['shop_url'] = 'https:' + info.xpath('div[@class="p-detail"]/dl[2]/dd/a/@href').extract_first()
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(item['book_url'],callback=self.parse_price_info,headers=headers,meta={'item':item_copy})
        next_url = 'https:' + response.xpath('//a[@class="pn-next"]/@href').extract_first()
        if not next_url:
            a_headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
            yield scrapy.Request(next_url,callback=self.parse_book_name_book_jd,headers=a_headers,meta={'item':item_bak})


    def parse_detail(self,response):
        #处理书名等等信息
        item = response.meta['item']
        all_name_and_url = response.xpath('//div[contains(@class,"p-name")]')
        all_img = response.xpath('//div[contains(@class,"p-img")]')
        for name_url,img in zip(all_name_and_url,all_img):
            headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
            book_name = name_url.xpath('./a/em/text()').extract_first()
            book_url = name_url.xpath('./a/@href').extract_first()
            try:
                img_url = 'http:' + img.xpath('./a/img/@src').extract_first()
            except:
                img_url = 'http:' + img.xpath('./a/img/@data-lazy-img').extract_first()
            shop_name = name_url.xpath('./..//a[@class="curr-shop hd-shopname"]/@title').extract_first()
            shop_url = name_url.xpath('./..//a[@class="curr-shop hd-shopname"]/@href').extract_first()
            if shop_name == None:
                shop_name = '京东自营'
            item['book_name'] = book_name
            item['book_url'] = 'https:' + book_url
            item['img_url'] = img_url
            item['shop_name'] = shop_name
            if shop_url == None:
                item['shop_url'] = '无'
            else:
                item['shop_url'] = 'https:' + shop_url
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(item['book_url'],callback=self.parse_price_info,headers=headers,meta={'item':item_copy})

    def parse_price_info(self,response):
        item = copy.deepcopy(response.meta['item'])
        headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
        cat = re.findall(r'cat: \[(.*?)\]',response.text)[0]
        try:
            if 'e.jd.com' in response.url:
                sku_id = re.findall(r'e\.jd\.com/(.*?)\.html')
            else:
                sku_id = re.findall(r'item\.jd\.com/(.*?)\.html', response.url)[0]
        except:
            logging.warning(f'url: {response.url} 获取商品失败')
        cookies = response.request.headers.get('Cookie').decode()
        _ = str(execjs.eval('new Date().getTime()'))
        vender_id = re.findall(r'venderId:(.*?),',response.text)[0]
        #area默认是1_72_2799_0，0是不变的
        #按照地区不同可以修改
        #这里找到地区信息，例如北京为1，朝阳区为72
        #https://search.jd.com/script/search_new.init.js?2020-07-23-12!
        #fid填入对应的区(县，州，市)id，找到对应地域id即可
        #https://fts.jd.com/area/get?fid=fid&callback=jQuery2902877&_=1602205021116
        area = re.findall(r'ipLoc-djd=(.*?)&',cookies+'&')[0].replace('-','_')
        url = 'https://c.3.cn/book?skuId=' + sku_id + '&cat=' + quote(cat) + '&area=' + area + '&_=' + _
        yield scrapy.Request(url,callback=self.parse_price,headers=headers,meta={'item':item,'sku_id':sku_id,'vender_id':vender_id,'cat':cat,'area':area})

    def parse_price(self,response):
        item = copy.deepcopy(response.meta['item'])
        sku_id = response.meta['sku_id']
        headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
        all_data = response.json()
        vender_id = response.meta['vender_id']
        url_stock = 'https://c0.3.cn/stock?skuId=' + sku_id + '&cat=' + response.meta['cat'] + '&venderId=' + vender_id + '&area=' + response.meta['area'] + '&buyNum=1&choseSuitSkuIds=&extraParam={%22originid%22:%221%22}&ch=1&fqsp=0&pduid='
        try:
            #部分是有电子书的，所以需要获取电子书的价格
            item['price'] = all_data['m']
            item['e_book_price'] = all_data['p']
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(url_stock,callback=self.parse_no_e_book_sku,headers=headers,meta={'item':item_copy,'sku_id':sku_id})
        except:
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(url_stock,callback=self.parse_no_e_book_sku,headers=headers,meta={'item':item_copy,'sku_id':sku_id})

    def parse_no_e_book_sku(self,response):
        item = copy.deepcopy(response.meta['item'])
        sku_id = response.meta['sku_id']
        headers = {'user-agent': random.choice(self.settings['UA_LIST'])}
        _ = str(execjs.eval('new Date().getTime()'))
        url_comment = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds=' + sku_id + '&_=' + _
        all_data = response.json()
        #能获取到电子书,只需要获取一个是否有货即可
        if item.get('e_book_price'):
            item['stock_state'] = all_data['stock']['StockStateName']
        else:
            item['price'] = all_data['stock']['jdPrice']['p']
            item['e_book_price'] = 'no e-book'
            item['stock_state'] = all_data['stock']['StockStateName']
        item_copy = copy.deepcopy(item)
        yield scrapy.Request(url_comment,callback=self.parse_comment,headers=headers,meta={'item':item_copy})

    def parse_comment(self,response):
        #获取评论数
        item = copy.deepcopy(response.meta['item'])
        try:
            all_data = response.json()['CommentsCount'][0]
        except:
            logging.warning(f'url： {response.url}  获取评论数失败')
            return
        item['comment_count'] = int(all_data['CommentCount'])
        item['good_count'] = int(all_data['GoodCount'])
        item['good_rate'] = float(all_data['GoodRate'])
        item['poor_count'] = int(all_data['PoorCount'])
        yield item



