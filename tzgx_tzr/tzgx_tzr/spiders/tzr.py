# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from tzgx_tzr.items import tzgx_tzrItem


class TzrSpider(scrapy.Spider):
    name = 'tzr'
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
                "account": "18502828078",
                "password": "123456",
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
                    'topic': 'authorizations',  # 上市
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
                ':path': '/api/persons',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8',
                'authorization': json.loads(response.text)['data']['token']
            }

            contents = [
                {
                    'topic': 'persons',  # 融资
                    'url': 'https://www.itjuzi.com/api/persons'
                }
            ]
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "total": 8020,
                        "per_page": 20,
                        "page": str(pagenum + 1),
                        "scope": [],
                        "sub_scope": "",
                        "round": [],
                        "prov": "",
                        "city": [],
                        "status": "",
                        "type": 3,
                        "selected": "",
                        "location": "",
                        "hot_city": ""}
                    yield scrapy.FormRequest(content['url'], meta=content, body=json.dumps(data), method='POST',
                                             headers=header, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                item = tzgx_tzrItem()
                item['name'] = investevent['name']
                item['company'] = ''
                item['job'] = ''
                for type in investevent['type']:
                    item['job'] = item['job'] + type['name']
                item['description'] = investevent['des']
                item['website'] = 'IT桔子'
                item['link'] = 'https://www.itjuzi.com/person/' + \
                    str(investevent['id'])
                item['investment_field'] = ''
                for invse in investevent['invse_scope']:
                    item['investment_field'] = item['investment_field'] + \
                        invse['name']
                item['investment_stage'] = ''
                for invse in investevent['invse_round']:
                    item['investment_stage'] = item['investment_field'] + \
                        invse['name']
                item['content'] = investevent['des']
                item['spider_name'] = 'tzr'
                item['module_name'] = 'IT桔子-投资人'
                url = 'https://www.itjuzi.com/api/persons/'+str(investevent['id'])
                yield scrapy.Request(url, callback=self.parse_item, meta=item, dont_filter=True)
            except Exception as e:
                logging.error(
                    self.name +
                    " in parse_item: url=" +
                    response.request.url +
                    ", exception=" +
                    e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            investevents = json.loads(response.text)['data']
            response.meta['company'] = investevents['invst'][0]['name']
            response.meta['job'] = investevents['invst'][0]['position']
            item = response.meta
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
