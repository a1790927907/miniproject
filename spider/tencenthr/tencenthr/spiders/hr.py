import scrapy
import random
import logging
logger = logging.getLogger(__name__)

ua_list = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36','Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50','Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50']

class HrSpider(scrapy.Spider):
    name = 'hr'
    allowed_domains = ['careers.tencent.com']
    start_urls = ['https://careers.tencent.com/tencentcareer/api/post/ByCategories?timestamp=1601608918451&language=zh-cn']

    #flag为0时，停止当前循环，开始下一页的爬取
    flag = 1
    #页数设置
    page_count = 1
    #是否是下一次循环
    is_next = False
    def parse(self, response):
        all_category_data = response.json()
        all_category_list = []
        for category in all_category_data['Data']:
            all_category_dict = {}
            all_category_dict['id'] = category['CategoryId']
            all_category_dict['name'] = category['CategoryName']
            all_category_list.append(all_category_dict)

        previous = 0
        for i in all_category_list:
            print(i)
            self.flag = 1
            self.page_count = 1
            if previous != all_category_list.index(i):
                self.is_next = True
                previous = all_category_list.index(i)
            else:
                self.is_next = False
            while True:
                #使用随机请求头
                headers = {'user-agent':random.choice(ua_list)}
                hr_info_url = 'https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=' +  str(i['id']) +'&attrId=&keyword=&pageIndex='+ str(self.page_count) +'&pageSize=10&language=zh-cn&area=cn'
                self.page_count += 1

                #判断是否是下一次循环
                if self.is_next:
                    if self.page_count >= 5:
                        #在5页之后再重置下一次循环的判断，解决多线程间的变量共享
                        self.is_next = False

                if not self.flag:
                    logger.warning(f'当前类别为{i["name"]},共存储{self.page_count}页数据')
                    break
                import time
                time.sleep(random.uniform(0.3,0.6))
                yield scrapy.Request(hr_info_url,callback=self.parse_hr_info,headers=headers,meta={'category_dict':i})

    def parse_hr_info(self,response):
        category_dict = response.meta['category_dict']
        data = response.json()

        #先判断是否循环了一次
        #严格按照循环次数来设置类属性中的flag
        if not self.is_next:
            if data['Data']['Posts'] == None:
                self.flag = 0
                return
        try:
            for job_data in data['Data']['Posts']:
                items = {}
                items['category_id'] = category_dict['id']
                items['category_name'] = category_dict['name']
                items['job_name'] = job_data['RecruitPostName']
                items['country'] = job_data['CountryName']
                items['city'] = job_data['LocationName']
                items['url'] = job_data['PostURL']
                items['responsibility'] = job_data['Responsibility']
                yield items
        except:
            pass














