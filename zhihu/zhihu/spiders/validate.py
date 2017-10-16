# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/10/14 14:17'
import pymongo


class Validator(object):
    def __init__(self, db_url, db_name):
        self.client = pymongo.MongoClient(db_url)
        self.db = self.client[db_name]
        self.collect = self.db.user

    def exist_user(self, url_token):
        return self.collect.find({'url_token': url_token}).count() > 0

    def user_num(self):
        return self.collect.find().count()
