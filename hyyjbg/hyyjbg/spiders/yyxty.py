# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from hyyjbg.items import hyyjbgItem
from utils.tools.attachment import get_times
class YyxtySpider(scrapy.Spider):
    name = 'yyxty'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
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
                'pageIndex': '1',
                'pageSize': '5000',
                'i': '0',
                'OrderBy': 'C_ADDTIME DESC'}

            contents = [
                {
                    'topic': 'yyxtw',  # 用益信托网
                    'url': 'http://www.yanglee.com/Action/GetResearchList.ashx'
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(content['url'], cb_kwargs=content, formdata=data, method='POST',
                                         headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                                         callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        data = json.loads(response.text.replace('pageIndex', '"pageIndex"'))
        for obj in data['result']:
            try:
                url = 'http://www.yanglee.com/research/Details.aspx?i=' + \
                      str(obj['C_ID'])
                result = {
                    "url": url,
                    "title": obj['C_TITLE'],
                    "time": obj['C_ADDTIME']
                }
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = hyyjbgItem()
            item['title'] = kwargs['title']
            item['date'] = kwargs['time']
            item['resource'] = ''
            item['content'] = response.css('.article-con').extract_first()
            item['website'] = '用益信托易'
            item['link'] = kwargs['url']
            item['spider_name'] = 'yyxty'
            item['txt'] = ''.join(response.css('.article-con *::text').extract())
            item['module_name'] = '信托融资一行业基本报告-用益信托易'
            item['date'] = get_times(item['date'])
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