# -*- coding: utf-8 -*-
import scrapy
from threading import Timer
import logging

from scrapy_splash import SplashRequest
import time
from utils.tools.attachment import get_attachments,get_times

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

url = 'http://r.cnki.net/KNS/request/SearchHandler.ashx'
data = {
    "curpage": "1",
    "RecordsPerPage": "5000",
    "turnpage": "1",
    "tpagemode": "U",
    "dbPrefix": "KJBG",
    "Fields": "",
    "DisplayMode": "custommode",
    "PageName": "ASP.brief_result_aspx",
    "tokenstr": "uYuiM7d8Lar9/GrSpqt4gR7rokDxJTJ0jTLIwEPGxJWaGQAQssY3C+e8io/rEAwlcbkXGLmmD4Kdrk1jumRhr1bpx5YqtjXmEVqL/mmo593pbCNqblIp7x18fLpo0CSnzqxMwRd3jFGrYS/MZjsw5oDPwKTvn7a27Eg/u6UhUbijwEdmo9Jh5MzCUvh3YDGuDPZg6ShAXiab8kBoNbLGgrZ4JwdU0QGPnZ8FXz2V3rGoApXBsjyotfj2p4bphfGkQcsF/mb4D9E1lEOsrfqpfDahp1X5wJXC1XKiHszF+T6KO60BSfxEjm+dvO8oFwLxFhVo9Uup4x/pJQANNKzKCos0Vla4qyBI6EgxrfSplyigiN9M55QwC9pfudgH7RruV4PJhwAvqzIxGaoEkkwfTeDn7owEIKNK",
    "sortcode": "43782",
    "sortorder": "desc",
    "__": "Fri Jan 10 2020 22:24:31 GMT+0800 (中国标准时间)"
}
header = {
    'Content-Type': 'application/x-www-form-urlencoded'
}
class KjbgSpider(scrapy.Spider):
    name = 'test'

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum
    def test_page(self,text):
        print(text)
    def start_requests(self):
        try:
            for num in range(30):
                data['curpage'] = str(num)
                # if num > 0 and num%10 == 0:
                #     time.sleep(120)
                yield scrapy.FormRequest(url, formdata=data,
                     headers=header,
                     callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self,response):
        print(len(response.xpath('//*[@class="s-result"]/div')))