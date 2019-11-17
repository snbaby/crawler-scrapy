# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem

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
    name = 'beijing-zfwj'
    custom_settings = {
        'SPIDER_MIDDLEWARES':{
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 100,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 64,
        },

        'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE':'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL' :'http://localhost:8050/'
    }
    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://www.beijing.gov.cn/zhengce/zhengcefagui/index.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())

    def parse_page(self, response):
        page_count  = self.parse_pagenum(response)
        try:
            for pagenum in range(page_count):
                url = "http://www.beijing.gov.cn/zhengce/zhengcefagui/index_" + str(pagenum) +".html"
                yield  SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                self.add_pagenum =  int(response.xpath('//div[@class="changepage"]').re('([1-9]\d*\.?\d*)')[0])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())

    def parse_one_pagenum(self, response):
        try:
            url = 'http://sousuo.gov.cn/column/30469/1.htm'
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())

    def parse(self, response):
        for href in response.xpath('//ul[@class="list"]/li/a/@href'):
            try:
                print(href.extract()[1:])
                yield scrapy.Request("http://www.beijing.gov.cn/zhengce/zhengcefagui" + href.extract()[1:],
                                     callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        try:
            item = rmzfzcItem()
            item['title'] = response.xpath('//div[@class="header"]/p/text()').extract_first().strip()
            item['article_num'] = response.xpath('//*[@id="mainText"]/p[1]/text()').extract()[0] if response.xpath('//*[@id="mainText"]/p[1]/text()').extract() else response.xpath('//*[@id="mainText"]/div/p[1]/text()').extract()[0]
            item['content'] = response.text
            item['source'] = ''
            item['time'] = response.xpath('/html/body/div[3]/div/ol/li[8]/span/text()').extract_first()
            item['province'] = '北京市'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '北京市人民政府'
            item['link'] = response.request.url
            appendix = []
            # for href in response.xpath('.relevantdoc.xgjd a::href'):
            #    appendix.append(href.extract())
            item['appendix'] = appendix
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
        yield item