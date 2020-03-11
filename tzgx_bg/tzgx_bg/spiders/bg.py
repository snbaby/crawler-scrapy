# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from tzgx_bg.items import tzgx_bgItem
from utils.tools.attachment import get_times

class BgSpider(scrapy.Spider):
    name = 'bg'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            data = {
                "account": "17716154415",
                "password": "ly123456",
                "type": "pswd"}

            header = {
                ':authority': 'www.itjuzi.com',
                ':method': 'POST',
                ':path': '/api/authorizations',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8'
            }

            contents = [
                {
                    'topic': 'authorizations',  # 融资
                    'url': 'https://www.itjuzi.com/api/authorizations'
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(content['url'], meta=content, body=json.dumps(data), method='POST',
                                         headers=header,
                                         callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = self.parse_pagenum(response)
        try:
            header = {
                ':authority': 'www.itjuzi.com',
                ':method': 'POST',
                ':path': '/api/investevents',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8',
                'authorization': json.loads(response.text)['data']['token']
            }

            contents = [
                {
                    'topic': 'investevents',  # bingou
                    'url': 'https://www.itjuzi.com/api/investevents'
                }
            ]
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "total": 0,
                        "per_page": 20,
                        "page": pagenum + 1,
                        "type": 4,
                        "scope": "",
                        "sub_scope": "",
                        "round": "合并",
                        "valuation": [],
                        "valuations": "",
                        "ipo_platform": "",
                        "equity_ratio": "",
                        "status": "",
                        "prov": "",
                        "city": [],
                        "time": [],
                        "selected": "",
                        "location": "",
                        "hot_city": "",
                        "currency": [],
                        "keyword": ""}

                    data1 = {
                        "total": 0,
                        "per_page": 20,
                        "page": pagenum + 1,
                        "type": 3,
                        "scope": "",
                        "sub_scope": "",
                        "round": "收购",
                        "valuation": [],
                        "valuations": "",
                        "ipo_platform": "",
                        "equity_ratio": "",
                        "status": "",
                        "prov": "",
                        "city": [],
                        "time": [],
                        "selected": "",
                        "location": "",
                        "hot_city": "",
                        "currency": [],
                        "keyword": ""}
                    yield scrapy.FormRequest(content['url'], meta={'topic': 'hb', 'authorization': json.loads(response.text)['data']['token']}, body=json.dumps(data), method='POST', headers=header, callback=self.parse, dont_filter=True)
                    yield scrapy.FormRequest(content['url'], meta={'topic': 'sg', 'authorization': json.loads(response.text)['data']['token']}, body=json.dumps(data1), method='POST', headers=header, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 3
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                if response.meta['topic'] == 'hb':
                    acquirer = investevent['merger_rel_invst'][0]['name']
                    acquirerd = investevent['merger_rel_invst'][1]['name']
                    status = investevent['status']
                    industry = ''
                    for mergerRelInvst in investevent['merger_rel_invst']:
                        industry = industry + \
                            mergerRelInvst['cat_name'] + '-' + mergerRelInvst['sub_cat_name']
                    link = 'https://www.itjuzi.com/api/acquisition/' + \
                        str(investevent['id'])
                    result = {
                        'acquirer': acquirer,
                        'acquirerd': acquirerd,
                        'status': status,
                        'industry': industry,
                        'link': link,
                    }
                    header = {
                        ':authority': 'www.itjuzi.com',
                        ':method': 'GET',
                        ':path': '/api/acquisition/' + str(investevent['id']),
                        ':scheme': 'https',
                        'content-type': 'application/json;charset=UTF-8',
                        'accept': 'application/json, text/plain, */*',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'authorization': response.meta['authorization']
                    }
                    yield scrapy.FormRequest(link, headers=header, method='GET', callback=self.parse_hb, meta=result, dont_filter=True)
                else:
                    acquirer = investevent['acquirer'][0]['name']
                    acquirerd = investevent['merger_name']
                    status = investevent['status']
                    industry = investevent['merger_scope']
                    involving_equity = investevent['money']
                    link = 'https://www.itjuzi.com/api/merger/' + \
                        str(investevent['id'])
                    result = {
                        'acquirer': acquirer,
                        'acquirerd': acquirerd,
                        'status': status,
                        'industry': industry,
                        'involving_equity': involving_equity,
                        'link': link
                    }
                    header = {
                        ':authority': 'www.itjuzi.com',
                        ':method': 'GET',
                        ':path': '//api/merger/' + str(investevent['id']),
                        ':scheme': 'https',
                        'content-type': 'application/json;charset=UTF-8',
                        'accept': 'application/json, text/plain, */*',
                        'accept-language': 'zh-CN,zh;q=0.9',
                        'authorization': response.meta['authorization']
                    }
                    yield scrapy.FormRequest(link, headers=header, method='GET', callback=self.parse_sg, meta=result, dont_filter=True)
            except Exception as e:
                logging.error(
                    self.name +
                    " in parse_item: url=" +
                    response.request.url +
                    ", exception=" +
                    e.__str__())
                logging.exception(e)

    def parse_hb(self, response):
        data = json.loads(response.text)['data']
        print(data)
        try:
            item = tzgx_bgItem()
            item['title'] = data['merger_title']
            item['acquirer'] = response.meta['acquirer']
            item['acquirerd'] = response.meta['acquirerd']
            item['status'] = response.meta['status']
            item['industry'] = response.meta['industry']
            item['involving_equity'] = ''
            start_time = str(data['prev_id']['merger_show_year']) + '-' + str(data['prev_id']['merger_show_month']) + '-' + str(data['prev_id']['merger_show_day'])
            item['start_time'] = get_times(start_time)
            item['end_time'] = ''
            item['supported_vc_pe'] = ''
            item['website'] = 'IT桔子'
            item['link'] = response.meta['link']
            item['content'] = data['merger_des']
            item['spider_name'] = 'bg'
            item['module_name'] = 'IT桔子-并购'
            print(
                "===========================>crawled one item" +
                response.request.url)
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item

    def parse_sg(self, response):
        data = json.loads(response.text)['data']
        try:
            item = tzgx_bgItem()
            item['title'] = data['merger_title']
            item['acquirer'] = response.meta['acquirer']
            item['acquirerd'] = response.meta['acquirerd']
            item['status'] = response.meta['status']
            item['industry'] = response.meta['industry']
            item['involving_equity'] = response.meta['involving_equity']
            start_time = str(data['prev_id']['merger_show_year']) + '-' + str(
                data['prev_id']['merger_show_month']) + '-' + str(data['prev_id']['merger_show_day'])
            item['start_time'] = get_times(start_time)
            item['end_time'] = ''
            item['supported_vc_pe'] = ''
            item['website'] = 'IT桔子'
            item['link'] = response.meta['link']
            item['content'] = data['merger_des']
            item['spider_name'] = 'bg'
            item['module_name'] = 'IT桔子-并购'
            print(
                "===========================>crawled one item" +
                response.request.url)
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item
