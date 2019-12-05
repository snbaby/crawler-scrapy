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
    name = 'shorong_zfwj'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}
    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        urlList = ['http://www.shorong.gov.cn/col/col2266/index.html?uid=6820&pageNum=','http://www.shorong.gov.cn/col/col2262/index.html?uid=5836&pageNum=']
        try:
            for urlTmp in urlList:
                url = urlTmp+"1"
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page,cb_kwargs={'preUrl':urlTmp})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count  = int(self.parse_pagenum(response))
        try:
            preUrl = kwargs['preUrl']
            for pagenum in range(page_count):
                url = preUrl + str(pagenum)
                yield  SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        print(response.text)
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                self.add_pagenum = response.css("#toPage li::text").extract_first()[1:-1]
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//ul[@class="listTxt"]/li/h4/a/@href'):
            try:
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
            item['title'] = response.css('.oneColumn h1::text').extract_first().strip()
            item['article_num'] = ''
            item['content'] = "".join(response.xpath('//div[@id="UCAP-CONTENT"]').extract())
            item['appendix'] = ''
            item['source'] = response.xpath('//div[@class="pages-date"]//span[contains(text(),"来源")]/text()').extract_first().replace('来源：','')
            item['time'] = response.xpath('//div[@class="pages-date"]/text()').extract_first()
            item['province'] = '山东省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '山东省人民政府'
            item['module_name'] = '山东省人民政府-政府文件'
            item['spider_name'] = 'shorong_zfwj'
            item['txt'] = "".join(response.xpath('//div[@id="UCAP-CONTENT"]//text()').extract())
            item['appendix_name'] = ''
            item['link'] = response.request.url
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
