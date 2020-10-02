import scrapy
import random
import re
import logging
from sunpolicy.items import SunpolicyItem
ua_list = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50','Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50']

logger = logging.getLogger(__name__)
class SunSpider(scrapy.Spider):
    name = 'sun'
    allowed_domains = ['sun0769.com']
    start_urls = ['http://wz.sun0769.com/political/index/politicsNewest']
    page_count = 1

    def parse(self, response):
        all_class_labels = response.css("[class='department-ul clear department-ul-sty mr-three'] li")
        all_labels = []
        all_name = []
        for labels in all_class_labels:
            name = {}
            all_labels.append('http://wz.sun0769.com' + labels.re_first(r'href="(.*?)"'))
            name['name'] = labels.re_first(r'<a.*?>(.*?)</a>')
            all_name.append(name)

        #遍历所有类别
        for l,n in zip(all_labels,all_name):
            headers = {'user-agent':random.choice(ua_list)}
            yield scrapy.Request(l,callback=self.parse_sun_info,headers=headers,meta={'all_name':n})

    def parse_sun_info(self,response):
        all_name = response.meta

        #判断当前页和下一页是否一致
        try:
            judge_url = response.meta['next_url']
            judge_url += '&'
            current_page = int(re.findall(r'page=(.*?)&',judge_url)[0])
            next_page_str = response.css('[class="arrow-page prov_rota"]').re_first(r'href="(.*?)"').replace('amp;',"") + '&'
            next_page = int(re.findall(r'page=(.*?)&',next_page_str)[0])

            if current_page != next_page - 1:
                return
        except:
            pass


        #获取当前类别下所有的问政的信息对象
        li_list = response.css('[class="clear"]')

        for li in li_list:
            headers = {'user-agent': random.choice(ua_list)}
            item = SunpolicyItem()
            item['category'] = all_name['all_name']['name']

            # print(li.css('[class="state2"]').extract_first())
            item['status'] = re.findall(r'<span.*?>(.*?)</span>',li.css('[class="state2"]').extract_first(),re.S)[0].replace(' ','').replace('\n','').replace('\t','')

            item['title'] = li.css('[class="color-hover"]').re_first(r'<a.*?>(.*?)</a>')

            item['url'] ='http://wz.sun0769.com' + li.css('[class="color-hover"]').re_first(r'href="(.*?)"')

            #其中一个类别没有响应时间
            try:
                item['reponsetime'] = re.findall(r'<span.*?>(.*?)</span>',li.css('[class="state4"]').extract_first(),re.S)[0].replace(' ','').replace('\n','').replace('\t','')
            except:
                item['reponsetime'] = ''

            item['querytime'] = li.css('[class="state5 "]').re_first('<span.*?>(.*?)</span>')

            yield scrapy.Request(item['url'],callback=self.parse_detail,headers=headers,meta={'item':item})

        headers = {'user-agent':random.choice(ua_list)}

        #获取下一页的url
        next_url ='http://wz.sun0769.com' +  response.css('[class="arrow-page prov_rota"]').re_first(r'href="(.*?)"')
        next_url = next_url.replace('amp;','')

        log_data = next_url + '&'
        log = re.findall(r'page=(.*?)&',log_data)[0]
        try:
            logger.warning(f"当前分类{all_name['all_name']['name']},第{log}页")
        except:
            logger.error(f'分类{all_name["all_name"]["name"]}保存失败!')

        #防止反爬，加长操作时间
        import time
        time.sleep(random.uniform(2,4))
        yield scrapy.Request(next_url,callback=self.parse_sun_info,headers=headers,meta={'next_url':next_url,'all_name':all_name['all_name']})

    def parse_detail(self,response):
        #提取详情页内容
        item = response.meta['item']
        content = response.css('[class="details-box"]').re_first(r'<pre>(.*?)</pre>')
        #无内容显示None
        item['content'] = content
        img_list = response.css('[class="clear details-img-list Picture-img"]').re(r'src="(.*?)"')
        #无图片显示空列表
        item['img_url_list'] = img_list
        yield item






