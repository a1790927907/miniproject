import scrapy
from suning.items import SuningItem
import random,re
import json
import copy
ua_list = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50','Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50']


class SnbookSpider(scrapy.Spider):
    name = 'snbook'
    allowed_domains = ['book.suning.com','list.suning.com','product.suning.com','pas.suning.com']
    start_urls = ['https://book.suning.com/']

    def parse(self, response):
        #一级大标题获取
        all_first_title_ele = response.css('[class="menu-item"]>dl>dt')
        #包含二级标题
        all_second_title_ele = response.css('[class="menu-sub"]>[class="submenu-left"]')
        for first_title,second_title in zip(all_first_title_ele,all_second_title_ele):
            item = SuningItem()
            title = first_title.css('h3>a').re_first(r'<a.*?>(.*?)</a>')
            item['first_title'] = title
            for st,tt in zip(second_title.css('[class="submenu-item"]'),second_title.css('[class="book-name-list clearfix"]')):
                #获取二级标题
                item['second_title'] = st.re_first(r'<a.*?>(.*?)</a>')
                #遍历二级标题下的所有小标题
                for li in tt.css('li'):
                    headers = {'user-agent':random.choice(ua_list)}
                    item['third_title'] = li.re_first(r'<a.*?>(.*?)</a>')
                    item['class_url'] = li.re_first(r'href="(.*?)"')
                    #以下全部使用深拷贝避免变量共享问题
                    item_copy = copy.deepcopy(item)
                    item_copy1 = copy.deepcopy(item)
                    yield scrapy.Request(item['class_url'],callback=self.parse_book_title,headers=headers,meta={'item_copy':item_copy,'item_copy1':item_copy1})


    def parse_book_title(self,response):
        #两个一样的，随意用
        item = response.meta['item_copy']
        item_copy = response.meta['item_copy1']

        #获取总页数
        all_page = int(response.css('#bottom_pager>a[pagenum]').re(r'<a.*?>(.*?)</a>')[-1])
        #获取当前小分类id
        book_class_id = int(re.findall(r'1-(.*?)-0',item['class_url'])[0])

        #切换页数
        for page in range(all_page):
            headers = {'user-agent': random.choice(ua_list)}
            for i in range(2):
                if i == 0:
                    #前30个商品
                    url = 'https://list.suning.com/emall/showProductList.do?ci=' + str(book_class_id)  +'&pg=03&cp=' + str(page) + '&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAABC&id=IDENTIFYING&cc=021'
                else:
                    #后30个商品
                    url = 'https://list.suning.com/emall/showProductList.do?ci=' + str(book_class_id) + '&pg=03&cp=' + str(page) + '&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAABC&id=IDENTIFYING&cc=021&paging=1'

                yield scrapy.Request(url,callback=self.parse_another_books,headers=headers,meta={'item':item_copy})


    def parse_another_books(self,response):

        item = response.meta['item']

        #所有图书标题
        all_half_book_title = response.css('[class="sell-point"]>[class="sellPoint"]')
        #所有图书图片
        all_half_img = response.css('[class="img-block"]>[class="sellPoint"]')
        #所有图书的售卖门店
        all_sellers = response.css('[class="seller oh no-more "]>a')
        for half_book_title,half_img,sellers in zip(all_half_book_title,all_half_img,all_sellers):
            headers = {'user-agent': random.choice(ua_list)}
            book_title = re.findall(r'<a.*?>(.*?)<em',half_book_title.extract(),re.S)[0]

            img_url = 'http:' + half_img.re_first(r'src2="(.*?)"')
            item['book_title'] = book_title
            item['seller'] = sellers.re_first(r'<a.*?>(.*?)</a>')
            item['book_url'] = 'https:' + half_book_title.re_first(r'href="(.*?)"')
            item['img_url'] = img_url
            item_copy_in_another = copy.deepcopy(item)

            yield scrapy.Request(item['book_url'],callback=self.parse_params,headers=headers,meta={'item':item_copy_in_another})


    def parse_params(self,response):
        try:
            item = response.meta['item']

            headers = {'user-agent': random.choice(ua_list)}
            html_text = response.text
            passPartNumber = re.findall(r'"passPartNumber":"(.*?)"',html_text)[0]
            partNumber = re.findall(r'"partNumber":"(.*?)"',html_text)[0]
            vendorCode = re.findall(r'"vendorCode":"(.*?)"',html_text)[0]

            #获取价格以及运费
            price_url = 'https://pas.suning.com/nspcsale_0_'+ passPartNumber+'_'+ partNumber +'_'+ vendorCode +'_20_021_0210199_502282_1000267_9264_12113_Z001___R9011207_1.0________0___1.0_2__502320_502689_.html?callback=pcData'
            item_copy_in_params = copy.deepcopy(item)

            yield scrapy.Request(price_url,callback=self.parse_book_price,headers=headers,meta={'item':item_copy_in_params})
        except:
            return

    def parse_book_price(self,response):
        pcdata = response.text
        item = response.meta['item']

        try:
            json_data = re.findall(r'pcData\((.*)\)',pcdata,re.S)[0]
            json_convert = json.loads(json_data)
            price = json_convert['data']['price']['saleInfo'][0]['netPrice']
            freight = json_convert['data']['freightObj']['fare']
            item['price'] = price
            item['freight'] = freight
            yield item
        except:
            return





#https://pas.suning.com/nspcsale_0_000000010567465560_000000010567465560_0070216571_20_021_0210199_502282_1000267_9264_12113_Z001___R9011205_0.01________0___1.0_2__502320_502687_.html?callback=pcData&_=1601762724697

#https://pas.suning.com/nspcsale_0_00000000010567465560_00000000010567465560_0070216571_20_021_0210199_502282_1000267_9264_12113_Z001___R9011207_1.0________0___1.0_2__502320_502689_.html?callback=pcData



#https://list.suning.com/emall/showProductList.do?ci=502679&pg=03&cp=3&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAABC&id=IDENTIFYING&cc=021&paging=1&sub=0

#https://list.suning.com/emall/showProductList.do?ci=502679&pg=03&cp=3&il=0&iy=0&adNumber=0&n=1&ch=4&prune=0&sesab=ACBAABC&id=IDENTIFYING&cc=021





