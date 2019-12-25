# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
script ="""
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

class QuanguoZuixinSpider(scrapy.Spider):
    name = 'QuanguoZuixin'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
        'SPIDER_MIDDLEWARES':{
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

        'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE':'scrapy_splash.SplashAwareFSCacheStorage',
    }
    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://sousuo.gov.cn/column/30469/0.htm"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count  = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                url = "http://sousuo.gov.cn/column/30469/" + str(pagenum) +".htm"
                yield  SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return response.css("#toPage li::text").extract_first()[1:-1]
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_one_pagenum(self, response):
        try:
            url = 'http://sousuo.gov.cn/column/30469/1.htm'
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//ul[@class="listTxt"]/li/h4/a/@href'):
            try:
                print('>>>>>>>>>' + href.extract())
                yield scrapy.Request(href.extract(), callback=self.parse_item, dont_filter=True)
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
            item['title'] = response.css('.bd1 td::text').extract()[4] if response.css('.bd1 td::text') else ''
            item['article_num'] = response.css('.bd1 td::text').extract()[5]  if response.css('.bd1 td::text') else ''
            item['content'] = response.text
            item['appendix'] = appendix
            item['source'] = response.xpath('//div[@class="pages-date"]//span[contains(text(),"来源")]/text()').extract_first()
            item['time'] = response.css('.bd1 td::text').extract()[3]  if response.css('.bd1 td::text') else ''
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '中华人民共和国中央人民政府'
            item['module_name'] = '中华人民共和国中央人民政府-最新'
            item['spider_name'] = 'quanguo_zuixin'
            item['txt'] = "".join(response.xpath('//div[@id="UCAP-CONTENT"]//text()').extract())
            item['appendix_name'] = appendix_name
            item['time'] = get_times(item['time'])
            item['link'] = response.request.url
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
