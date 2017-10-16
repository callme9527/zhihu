# -*- coding: utf-8 -*-
import sys
import cPickle as pickle
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import json
import time
import scrapy

from yundama import get_pin
from scrapy import Request, FormRequest
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from zhihu.items import UserLoader, ZhihuItem


class ZhihuCrawlSpider(scrapy.Spider):
    name = 'zhihu_crawl'
    allowed_domains = ['zhihu.com']
    url = 'https://www.zhihu.com/people/imike'

    def start_requests(self):
        if os.path.exists('cookie.txt'):
            with open('cookie.txt', 'rb') as f:
                cookies = pickle.load(f)
            return [Request(self.url, cookies=cookies, meta={'cookiejar': 1, 'dont_merge_cookies': True}, callback=self.parse_user)]
        return [Request('https://www.zhihu.com/#signin', callback=self.login, meta={'cookiejar': 1})]

    def login(self, response):
        xsrf = response.xpath('.//input[@name="_xsrf"]/@value').extract_first()
        return FormRequest('https://www.zhihu.com/login/phone_num', callback=self.after_login,
                           meta={
                               'cookiejar': response.meta['cookiejar'],
                                'xsrf': xsrf
                           },
                           formdata={
                               '_xsrf': xsrf,
                               'phone_num': get_project_settings().get('USER'),
                               'password': get_project_settings().get('PWD'),
                               'captcha_type': 'cn'
                           })

    def after_login(self, response):
        con = json.loads(response.body)
        self.logger.info(con)
        if u'成功' in con.get('msg', ''):
            self.logger.info(u'login success')
            if not os.path.exists('cookie.txt'):
                # 保存cookie
                cookies = {}
                req_cookies = response.request.headers['cookie']
                for cookie in req_cookies.split(';'):
                    k, v = cookie.split('=', 1)
                    cookies[k] = v
                res_cookies = dict(response.headers)['Set-Cookie']
                self.logger.warning(res_cookies)
                for cookie in res_cookies:
                    cookie = cookie.split(';', 1)[0].strip()
                    k, v = cookie.split('=', 1)
                    cookies[k] = v
                with open('cookie.txt', 'wb') as f:
                    pickle.dump(cookies, f)
            return Request(self.url, callback=self.parse_user,
                           meta={'cookiejar': response.meta['cookiejar']})
        elif u'验证码' in con.get('msg', ''):
            self.logger.info(u'需要验证码')
            return Request('https://www.zhihu.com/captcha.gif?r=%d&type=login&lang=en'%(time.time()*1000),
                           meta={'cookiejar': response.meta['cookiejar'], 'xsrf': response.meta['xsrf']},
                           callback=self.login_withcap)
        elif u'密码' in con.get('msg', ''):
            self.logger.warning(u'账号密码错误')
            return

    def login_withcap(self, response):
        with open('pin.png', 'wb') as f:
            f.write(response.body)
        pin = get_pin(get_project_settings().get('DMUSER', ''), get_project_settings().get('DMPWD', ''))
        return FormRequest('https://www.zhihu.com/login/phone_num', callback=self.after_login,
                           meta={
                               'cookiejar': response.meta['cookiejar'],
                               'xsrf': response.meta['xsrf']
                           },
                           formdata={
                               '_xsrf': response.meta['xsrf'],
                               'phone_num': get_project_settings().get('USER'),
                               'password': get_project_settings().get('PWD'),
                               'captcha_type': 'en',
                               'captcha': pin
                           })

    def parse_user(self, response):
        l = UserLoader(item=ZhihuItem(), response=response)
        datas = response.xpath('.//div[@id="data"]/@data-state').extract_first()
        users = json.loads(datas)['entities']['users']
        for url_token, user_info in users.items():
            url_token = url_token; l.add_value('url_token', url_token)
            name = user_info['name']; l.add_value('name', name)
            gender = user_info['gender']
            gender = u'男' if gender == 1 else u'女' if gender == 0 else u'保密'; l.add_value('gender', gender)
            avatar_url = user_info['avatarUrl']; l.add_value('avatar_url', avatar_url)  # 头像
            headline = user_info.get('headline', u'无'); l.add_value('headline', headline)  # 名字后面的介绍
            description = user_info.get('description', u'无'); l.add_value('description', description)  # 个人简介
            business = user_info.get('business', {}).get('name', u'无'); l.add_value('business', business)  # 从事行业
            # 居住地
            locations = user_info.get('locations', [])
            if locations:
                for location in locations:
                    l.add_value('location', location.get('name', ''))
            else:
                l.add_value('location', u'无')
            # 教育经历
            educations = user_info.get('educations', [])
            if educations:
                for education in educations:
                    edu = []
                    school = education.get('school', {}).get('name', '')
                    if school: edu.append(school)
                    major = education.get('major', {}).get('name', '')
                    if major: edu.append(major)
                    l.add_value('education', edu)
            else:
                l.add_value('education', [])
            # 工作经历
            employments = user_info.get('employments', [])
            if employments:
                for employment in employments:
                    emp = []
                    company = employment.get('company', {}).get('name', '')
                    if company: emp.append(company)
                    job = employment.get('job', {}).get('name', '')
                    if job: emp.append(job)
                    l.add_value('employment', emp)
            else:
                l.add_value('employment', [])
            # 所获成就
            badges = user_info.get('badge', [])
            if badges:
                for badge in badges:
                    if not badge.get('topics', ''):continue
                    for topic in badge.get('topics'):
                        name = topic.get('name')
                        l.add_value('badge', name)
            else:
                l.add_value('badge', '')

            user_type = user_info['userType']; l.add_value('user_type', user_type)  # 用户类型
            follow_num = user_info.get('followingCount', 0); l.add_value('follow_num', follow_num)  # 关注数
            fans_num = user_info.get('followerCount', 0); l.add_value('fans_num', fans_num)  # 粉丝数
            id = user_info['id']; l.add_value('id', id)  # 用户id
            thanked_num = user_info.get('thankedCount', 0); l.add_value('thanked_num', thanked_num)  # 被感谢次数
            favorited_num = user_info.get('favoritedCount', 0); l.add_value('favorited_num', favorited_num)  # 被收藏次数
            vote_num = user_info.get('voteupCount', 0); l.add_value('vote_num', vote_num)  # 获得点赞数
            public_edit = user_info.get('logsCount', 0); l.add_value('public_edit', public_edit)  # 公告编辑次数
            article_num = user_info.get('articlesCount', 0); l.add_value('article_num', article_num)  # 发表文章数
            answer_num = user_info.get('answerCount', 0); l.add_value('answer_num', answer_num)  # 回答数
            question_num = user_info.get('questionCount', 0); l.add_value('question_num', question_num)  # 提问数
            pin_num = user_info.get('pinsCount', 0); l.add_value('pin_num', pin_num)  # 想法数
            column_num = user_info.get('columnsCount', 0); l.add_value('column_num', column_num)  # 专栏数
            live_num = user_info.get('hostedLiveCount', 0); l.add_value('live_num', live_num)  # live数
            yield l.load_item()

            follow_page = follow_num / 20 if follow_num % 20 == 0 else follow_num / 20 + 1
            for i in range(1, follow_page+1):
                follow_url = response.url+'/following?page='+str(i)
                yield Request(follow_url, callback=self.parse_relate, meta={'cookiejar': response.meta['cookiejar']})
            fans_page = fans_num / 20 if fans_num % 20 == 0 else fans_num / 20 + 1
            for i in range(1, fans_page+1):
                fans_url = response.url+'/followers?page='+str(i)
                yield Request(fans_url, callback=self.parse_relate, meta={'cookiejar': response.meta['cookiejar']})

    def parse_relate(self, response):
        links = response.xpath('.//a[@class="UserLink-link"]/@href').extract()
        links = set(links)
        for link in links:
            yield Request('https://www.zhihu.com'+link, callback=self.parse_user,
                          meta={'cookiejar': response.meta['cookiejar']})


if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(ZhihuCrawlSpider)
    process.start()
