# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join, Compose


class ZhihuItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    url_token = scrapy.Field()
    gender = scrapy.Field()
    avatar_url = scrapy.Field()
    headline = scrapy.Field()
    description = scrapy.Field()
    business = scrapy.Field()
    location = scrapy.Field()
    education = scrapy.Field()
    employment = scrapy.Field()
    badge = scrapy.Field()
    user_type = scrapy.Field()
    follow_num = scrapy.Field()
    fans_num = scrapy.Field()
    thanked_num = scrapy.Field()
    favorited_num = scrapy.Field()
    vote_num = scrapy.Field()
    public_edit = scrapy.Field()
    article_num = scrapy.Field()
    answer_num = scrapy.Field()
    question_num = scrapy.Field()
    column_num = scrapy.Field()
    pin_num = scrapy.Field()
    live_num = scrapy.Field()


def handle_compose_in(values):
    # print 'in:'+str(values)
    if not values: return u'无'
    return ':'.join(values)


class UserLoader(ItemLoader):
    default_output_processor = TakeFirst()

    badge_out = Join(',')

    education_in = Compose(handle_compose_in, stop_on_none=False)
    education_out = Join('|')

    employment_in = Compose(handle_compose_in, stop_on_none=False)
    employment_out = Join('|')
