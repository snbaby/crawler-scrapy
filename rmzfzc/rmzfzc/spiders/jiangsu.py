# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy_splash import SplashRequest

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))
  return {
    html = splash:html(),
  }
end
"""


class JiangsuSpider(scrapy.Spider):
    name = 'jiangsu'
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
            urls = [
                'http://www.jiangsu.gov.cn/col/col32646/index.html',
                'http://www.jiangsu.gov.cn/col/col32648/index.html',
                'http://www.jiangsu.gov.cn/col/col59202/index.html',
                'http://www.jiangsu.gov.cn/col/col66109/index.html'
            ]
            for url in urls:
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page, cb_kwargs={'url': url})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        uid = response.css('.bt-rig-cen-01 div::attr(id)').extract_first()
        print('-------------')
        print(response.cb_kwargs['url'])
        print(page_count)
        print(uid)
        print('-------------')
        return
        try:
            for pagenum in range(page_count):
                url = response.request.url + "?uid=" + \
                    uid + "&pageNum=" + str(pagenum)
                print(url)
                # yield SplashRequest(url, args={'lua_source': script, 'wait':
                # 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.default_pgTotalPage::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        pass
