# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

class QinghaiGgjyptSpider(scrapy.Spider):
    name = 'qinghai_ggjypt'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
            'scrapy_splash.SplashCookiesMiddleware': 140,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'gcjs',  # 工程建设
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001001/secondPage.html'
                },
                {
                    'topic': 'zfcg',  # 政府采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001002/secondPage.html'
                },
                {
                    'topic': 'ypcq',  # 药品采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001003/secondPage.html'
                },
                {
                    'topic': 'cqjy',  # 产权交易
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001004/secondPage.html'
                },
                {
                    'topic': 'kqjtd',  # 矿权及土地
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001005/secondPage.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
