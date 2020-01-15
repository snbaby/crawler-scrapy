# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from tzgx_rz.items import tzgx_rzItem


class RzSpider(scrapy.Spider):
    name = 'rz'
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
                "account": "18200111443",
                "password": "111111",
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
                yield scrapy.FormRequest(content['url'], cb_kwargs=content, body=json.dumps(data), method='POST',
                                         headers=header,
                                         callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = self.parse_pagenum(response, kwargs)
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
                    'topic': 'investevents',  # 融资
                    'url': 'https://www.itjuzi.com/api/investevents'
                }
            ]
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "total": 0,
                        "per_page": 20,
                        "page": pagenum + 1,
                        "type": 1,
                        "scope": "",
                        "sub_scope": "",
                        "round": [],
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
                    yield scrapy.FormRequest(content['url'], cb_kwargs=content, body=json.dumps(data), method='POST', headers=header, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 3
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                item = tzgx_rzItem()
                item['title'] = investevent['invse_title']
                item['financers'] = investevent['name']
                investors = ''
                for investor in investevent['investor']:
                    investors = investors + investor['name'] + ','
                item['investors'] = investors
                item['amount'] = investevent['money']
                item['rotation'] = investevent['round']
                item['time'] = str(investevent['year'])+'-'+str(investevent['month'])+'-'+str(investevent['day'])
                item['industry'] = investevent['com_scope']
                item['introduction'] = investevent['com_des']
                item['website'] = 'IT桔子'
                item['link'] = 'https://www.itjuzi.com/investevent/'+str(investevent['id'])
                item['content'] = investevent['invse_des']
                item['spider_name'] = 'rz'
                item['module_name'] = 'IT桔子-融资'
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
