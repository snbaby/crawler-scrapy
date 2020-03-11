# -*- coding: utf-8 -*-
import scrapy
import logging
import datetime
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
    name = 'zpks_qcwy'
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
         'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        page_count = 2001
        try:
            print(page_count)
            # 在解析翻页数之前，首先解析首页内容
            for pagenum in range(page_count):
                if pagenum > 0:
                    url = "https://search.51job.com/list/010000,000000,0000,00,9,99,%2B,2," + str(
                        pagenum) + ".html?lang=c&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&ord_field=0&dibiaoid=0&line=&welfare="
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse,
                                        dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)


    def parse(self, response):
        for href in response.xpath('//p[@class="t1 "]/span/a/@href').extract():
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
            item['job'] = response.xpath('//h1/@title').extract_first()
            item['company_name'] = response.xpath('//p[@class="cname"]/a/@title').extract_first()
            item['industry'] = ''.join(response.xpath('//p[@class="fp"]/a/text()').extract())
            item['location'] = location.replace('\xa0','') if location else ''
            item['salary'] = response.xpath('//div[@class="cn"]/strong/text()').extract_first()
            item['time'] = datetime.date.today()
            item['website'] = '前程无忧'
            item['link'] = response.request.url
            item['type'] = '2'
            item['source'] = '前程无忧'
            item['content'] = ''.join(response.xpath('//div[@class="bmsg job_msg inbox"]').extract())
            tmp = response.xpath('//*[@class="msg ltype"]//text()').extract()
            print(len(tmp))
            education = tmp[4].replace('\xa0','') if len(tmp) > 8 else ''
            item['education'] = education
            item['spider_name'] = 'qcwy'
            item['module_name'] = '前程无忧'
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
