import scrapy
import re
from bs4 import BeautifulSoup
from tieba.items import TiebaItem
import copy

class TbspiderSpider(scrapy.Spider):
    name = 'tbspider'
    allowed_domains = ['tieba.baidu.com']
    start_urls = ['https://tieba.baidu.com/f?ie=utf-8&kw=%E6%98%8E%E6%97%A5%E6%96%B9%E8%88%9F']

    def parse(self, response):
        #百度贴吧全是注释形式的html，所以response不能直接用css选择器，crawlspider也无法使用
        #提取出所有注释的html并且联结成一个html
        html_str_list = re.findall(r'<!--(.*?)-->',response.text,re.S)
        html_str = ''.join(html_str_list)
        bs = BeautifulSoup(html_str,'html.parser')
        all_article = bs.select('[class="t_con cleafix"]')
        for article in all_article:
            item = TiebaItem()
            bs_article = BeautifulSoup(str(article),'html.parser')
            title = re.findall(r'<a.*?>(.*?)</a>',str(bs_article.select('[class="j_th_tit"]')[0]))[0]
            detail_url = 'https://tieba.baidu.com' + re.findall(r'href="(.*?)"',str(bs_article.select('[class="j_th_tit"]')[0]))[0]
            #有些vip用户的class是不一样的
            try:
                auther = re.findall(r'title="主题作者: (.*?)"',str(bs_article.select('[class="tb_icon_author"]')[0]))[0]
            except:
                auther = re.findall(r'title="主题作者: (.*?)"',str(bs_article.select('[class="tb_icon_author no_icon_author"]')[0]))[0]
            item['title'] = title
            item['auther'] = auther
            item['detail_url'] = detail_url
            #获取id，可以通过id和评论外键关联
            article_id = int(detail_url.split('/')[-1])
            item['article_id'] = article_id
            #是否是置顶帖
            if bs_article.select('[class="icon-top"]') != []:
                item['is_top'] = 1
            else:
                item['is_top'] = 0
            item_copy = copy.deepcopy(item)
            yield scrapy.Request(item_copy['detail_url'],callback=self.parse_detail,meta={'item':item_copy})
        next_page_url = 'https:' + re.findall(r'href="(.*?)"',str(bs.select('[class="next pagination-item"]')[0]))[0].replace('amp;','')
        try:
            #若无法获取，则说明是最后一页
            last_page_url = 'https:' + re.findall(r'href="(.*?)"',str(bs.select('[class="last pagination-item"]')[0]))[0].replace('amp;','')
            yield scrapy.Request(next_page_url,callback=self.parse)
        except:
            return


    def parse_detail(self,response):
        item = response.meta['item']
        #获取主题的内容，第一个，评论的话是从第二个开始
        content = response.xpath('//div[@class="d_post_content j_d_post_content "]/text()').extract_first()
        item['content'] = content
        #获取主题的图片，同样是第一个
        author_img = response.xpath('//div[@class="d_post_content j_d_post_content "]')[0]
        #获取所有图片url地址列表形式
        img_list = list(author_img.xpath('./img[@class="BDE_Image"]/@src').extract())
        item['img_list'] = img_list
        upload_time = response.xpath('//div[@class="core_reply_tail clearfix"]//span[@class="tail-info"][last()]/text()').extract_first()
        item['upload_time'] = upload_time
        yield item

