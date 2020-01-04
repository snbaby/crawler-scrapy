# -*- coding: utf-8 -*-
import scrapy
import logging

from hyyjbg.items import hyyjbgItem
from utils.tools.attachment import get_times
class HxtSpider(scrapy.Spider):
    name = 'hxt'
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
            contents = [
                {
                    'topic': 'hxt',  # 好信坨
                    'url': 'http://www2.haoxintuo.com/index.php?a=lists&catid=19'
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
                    url = url + '&page=' + str(pagenum + 1)
                    yield scrapy.Request(url, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.pageindex::text').extract_first().replace(
                        '1/', ''))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for li in response.css('.schoolList li'):
            try:
                url = response.urljoin(
                    li.css('a::attr(href)').extract_first())
                title = li.css('a::text').extract_first()
                result = {
                    'url': url,
                    'title': title
                }
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = hyyjbgItem()
            item['title'] = kwargs['title']
            item['date'] = response.css('.newstl span::text').extract_first().split('浏览')[0].replace('发布时间：','').strip()
            item['resource'] = ''
            item['content'] = response.css('.newsCon').extract_first()
            item['website'] = '好信托'
            item['link'] = kwargs['url']
            item['spider_name'] = 'hxt'
            item['txt'] = ''.join(
                response.css('.newsCon *::text').extract())
            item['module_name'] = '信托融资一行业基本报告-好信托'
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

