# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from hyzx.items import hyzxItem

class JrjSpider(scrapy.Spider):
    name = 'jrj'
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
            contents = [
                {
                    'topic': 'jrj',  # 金融界
                    'url': 'http://trust.jrj.com.cn/list/hydt.shtml'
                }
            ]
            for content in contents:
                yield scrapy.Request(content['url'], callback=self.parse_page, cb_kwargs=content, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response, kwargs))
        try:
            for pagenum in range(page_count):
                url = kwargs['url']
                if pagenum == 0:
                    yield scrapy.Request(url, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
                else:
                    url = url.replace('.shtml', '-'+str(pagenum + 1) + '.shtml')
                    yield scrapy.Request(url, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 10
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('.ls3 a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = hyzxItem()
            item['title'] = ''.join(response.css('.titmain h1::text').extract()).strip()
            item['date'] = ''.join(response.css('.inftop span::text').extract()).split('来源：')[0].strip()
            item['resource'] = ''.join(response.css('.inftop span::text').extract()).split('来源：')[1].strip()
            item['content'] = response.css('.texttit_m1').extract_first()
            item['website'] = '金融界'
            item['link'] = kwargs['url']
            item['spider_name'] = 'jrj'
            item['txt'] = ''.join(response.css('.texttit_m1 *::text').extract())
            item['module_name'] = '信托融资一行业资讯-金融界'

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
