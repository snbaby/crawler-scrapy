# -*- coding: utf-8 -*-
import scrapy
import logging
import time

from scrapy_splash import SplashRequest
from zpks.items import zpksItem
script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class BeijingZfwjSpider(scrapy.Spider):
    name = 'zpks_boss'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': 'http://localhost:8050/'}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        page_count = 11
        try:
            print(page_count)
            # 在解析翻页数之前，首先解析首页内容
            for pagenum in range(page_count):
                if pagenum > 0:
                    time.sleep(1)
                    url = "https://www.zhipin.com/c101270100/?page="+str(pagenum)+"&ka=page-"+str(pagenum)
                    yield scrapy.Request(url,callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        print(response.text)
        for href in response.xpath('//h3[@class="name"]/a/@href').extract():
            try:
                print(href)
                yield scrapy.Request(href,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        try:
            item = zpksItem()
            temp = response.xpath('//p[@class="msg ltype"]/text()').extract()
            location = response.xpath('//p[@class="msg ltype"]/text()').extract_first()
            for dd in temp:
                if dd.find('发布')>-1:
                    times = dd.replace('发布','')

            item['job'] = response.xpath('//h1/@title').extract_first()
            item['company_name'] = response.xpath('//p[@class="cname"]/a/@title').extract_first()
            item['industry'] = ''.join(response.xpath('//p[@class="fp"]/a/text()').extract())
            item['location'] = location.replace('\xa0','') if location else ''
            item['salary'] = response.xpath('//div[@class="cn"]/strong/text()').extract_first()
            item['time'] = times.replace('\xa0','') if times else ''
            item['website'] = '前程无忧'
            item['link'] = response.request.url
            item['type'] = '2'
            item['source'] = '前程无忧'
            item['content'] = ''.join(response.xpath('//div[@class="bmsg job_msg inbox"]').extract())
            item['education'] = ''
            item['spider_name'] = 'qcwy'
            item['module_name'] = '前程无忧'
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
