# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
from zhihu.spiders.validate import Validator
from items import ZhihuItem


class ZhihuPipeline(object):
    def __init__(self, db_url, db_name):
        self.db_url = db_url
        self.db_name = db_name
        # self.validator = Validator(self.db_url, self.db_name)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('DBURL', 'mongodb://127.0.0.1:27017'),
                    crawler.settings.get('DBNAME', 'zhihu'))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.db_url)
        self.db = self.client[self.db_name]

    def process_item(self, item, spider):
        if isinstance(item, ZhihuItem):
            self.db['user'].update({'id': item['id']}, {'$set': dict(item)}, upsert=True)
        return item

    def close_spider(self, spider):
        self.client.close()
