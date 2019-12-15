# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
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


class TianJinZcjdSpider(scrapy.Spider):
    name = 'tianjin_zcjd'
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
        try:
            url = "http://www.tj.gov.cn/zw/zcjd/index.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                for pagenum in range(page_count):
                    url = "http://www.tj.gov.cn/zw/zcjd/index_" + \
                          str(pagenum) + ".html" if pagenum > 0 else "http://www.tj.gov.cn/zw/zcjd/index.html"
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse,
                                        dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                self.add_pagenum = int(response.xpath(
                    '/html/body/div[6]/div[2]/div[2]/table/tr/td/span').re('([1-9]\d*\.?\d*)')[2])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//ul[@class="ullist"]/li/a/@href'):
            try:
                yield scrapy.Request("http://www.tj.gov.cn/zw/zcjd" + href.extract()[1:],
                                     callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.xpath(
                '//*[@class="title"]/text()').extract_first().strip()
            item['article_num'] = ''
            item['content'] = "".join(
                response.xpath('//div[@id="zoom"]').extract())
            item['source'] = ''
            item['time'] = response.xpath(
                '//*[@class="time"]/span[2]/text()').extract_first().strip()[5:]
            item['province'] = '天津市'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '天津市人民政府'
            item['module_name'] = '天津市人民政府-政策解读'
            item['spider_name'] = 'tianjin_zcjd'
            item['txt'] = "".join(
                response.xpath('//div[@id="zoom"]//text()').extract())
            item['appendix_name'] = appendix_name
            item['link'] = response.request.url
            item['appendix'] = appendix
            item['time'] = get_times(item['time'])
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
