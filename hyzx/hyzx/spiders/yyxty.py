# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from hyzx.items import hyzxItem

class YyxtySpider(scrapy.Spider):
    name = 'yyxty'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            if not self.add_pagenum:
                data = {'pageIndex': '1','pageSize': '100000','i': '0','OrderBy': 'C_ADDTIME DESC'}
            else:
                data = {'pageIndex': '1','pageSize': str(self.add_pagenum*15),'i': '0','OrderBy': 'C_ADDTIME DESC'}

            contents = [
                {
                    'topic': 'yyxtw',  # 用益信托网
                    'url': 'http://www.yanglee.com/Action/GetInformationList.ashx'
                }
            ]
            print(str(data))
            for content in contents:
                yield scrapy.FormRequest(content['url'], formdata=data, method='POST',headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        # print(response.text)
        #jsonData = json.loads(response.text)
        logging.error(response.text)
        # num = int(int(jsonData['result']['totalcount']) / 20) + 1
        # num = 100
        # for n in range(num):
        #     data['pn'] = n * 20
        #     time.sleep(0.1)
        #     print(n)
        #     yield scrapy.Request(url, body=json.dumps(data), method='POST',
        #                          headers={'Content-Type': 'application/json'}, callback=self.parse_page)