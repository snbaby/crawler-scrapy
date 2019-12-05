# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

script = """
function main(splash)
    splash:go("www.baidu.com")
    splash:wait(1)
    return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'gansu'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES' : {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES' : {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE' : 'scrapy_splash.SplashAwareFSCacheStorage',
        # 'SPIDER_MIDDLEWARES': {
        #     'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        # },
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
        #     'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
        #     'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
        # },
        # 'ITEM_PIPELINES': {
        #     'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
        #     'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        # },
        # 'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'jyxxlb',  # 交易信息列表
                    'url': 'http://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/list'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint = 'execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url':"www.csdn.net",
                                    },
                                    callback=self.parse,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response,**kwargs):
        print('---------')
        print(response.text)
        pass
