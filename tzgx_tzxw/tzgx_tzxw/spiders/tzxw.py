# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from tzgx_tzxw.items import tzgx_tzxwItem


class TzxwSpider(scrapy.Spider):
    name = 'tzxw'
    custom_settings = {
        'CONCURRENT_REQUESTS': 30,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

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
                    'topic': 'authorizations',  # 投资机构
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
                ':path': '/api/news',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8',
                'authorization': json.loads(response.text)['data']['token']
            }

            contents = [
                {
                    'topic': 'news',  # 融资
                    'url': 'https://www.itjuzi.com/api/news'
                }
            ]
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "per_page": 20,
                        "page": str(pagenum + 1),
                        "type": 1,
                        "scope": [],
                        "time": [],
                        "news_type": [],
                        "keywords": ""}
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
                return 3560
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                result = {}
                result['title'] = investevent['title']
                result['source'] = investevent['main_url']
                result['date'] = investevent['year']
                result['content'] = ''
                result['website'] = 'it桔子'
                result['link'] = investevent['url']
                result['txt'] = ''
                result['spider_name'] = 'tzxw'
                result['module_name'] = 'IT桔子-投资新闻'
                yield scrapy.Request(investevent['url'], callback=self.parse_item, dont_filter=True, meta=result)
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
            item = tzgx_tzxwItem()
            item['title'] = response.meta['title']
            item['source'] = response.meta['source']
            item['date'] = response.meta['date']
            item['content'] = response.css('body').extract_first()
            item['website'] = 'it桔子'
            item['link'] = response.meta['link']
            item['txt'] = ''.join(response.css('body *::text').extract())
            item['spider_name'] = 'tzxw'
            item['module_name'] = 'IT桔子-投资新闻'
            print(
                "===========================>crawled one item" +
                response.request.url)
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)