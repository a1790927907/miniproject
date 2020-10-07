# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import pymysql
import json

#数据库密码
mysql_password = ''
#数据库用户名
mysql_username = ''
#数据库名
database_name = ''
class TiebaPipeline:
    flag = 0
    def open_spider(self,spider):
        self.mysql = pymysql.connect('localhost',mysql_username,mysql_password,database_name)
        self.cursor = self.mysql.cursor()

    def process_item(self, item, spider):
        item,judge = self.deal_with_info(item)
        if judge:
            sqlcmd = f'''insert into tbinfo values(0,'{item['title']}','{item['auther']}','{item['detail_url']}',{item['article_id']},{item['is_top']},'{item['content']}','{item['img_list']}','{item['upload_time']}')'''
            try:
                self.cursor.execute(sqlcmd)
                self.mysql.commit()
            except:
                self.mysql.rollback()
        return item

    def deal_with_info(self,info):
        #💞字符无法存入mysql,故需要去除
        for key in info:
            try:
                info[key] = info[key].replace('💞','')
            except:
                continue
        info['content'] = info['content'].strip()
        info['img_list'] = json.dumps(info['img_list'])
        # from datetime import datetime
        # info['upload_time'] = datetime.strptime(info['upload_time'],'%Y-%m-%d %H:%M')

        #去除重复的置顶帖
        if self.flag == 1:
            if self.info['title'] == info['title']:
                return (info,False)
        if info['is_top'] == 1 and self.flag == 0:
            self.info = info
            self.flag = 1
        return (info,True)

    def close_spider(self,spider):
        self.cursor.close()
        self.mysql.close()


