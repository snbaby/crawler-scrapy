# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class TianJinSzfwjSpider(scrapy.Spider):
    name = 'liaoning_ggjypt'
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
        try:
            url = "http://www.lnsggzy.com/003/secondpageDeal.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                temUrl = 'http://www.lnsggzy.com/003/secondpageDeal.html?categoryNum=003&pageIndex='
                url = temUrl + \
                      str(pagenum) if pagenum > 0 else "http://www.lnsggzy.com/003/secondpageDeal.html"
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            details = response.xpath('//div[@class="ewb-page"]/script').re(r'([1-9]\d*\.?\d*)')[4]
            pageCount = response.xpath('//div[@class="ewb-page"]/script').re(r'([1-9]\d*\.?\d*)')[3]
            if not self.add_pagenum:
                return int(details)/int(pageCount) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//li[@class="wb-data-list"]'):
            try:
                item = {}
                item['title'] = selector.xpath('./div/a/text()').extract_first()
                item['time'] = selector.xpath('./span/text()').extract_first()
                url = response.urljoin(selector.xpath('./div/a/@href').extract_first())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response, **kwargs):
        if response.text:
            try:
                category = '其他';
                title = kwargs['title']
                if title.find('招标') >= 0:
                    category = '招标'
                elif title.find('中标') >= 0:
                    category = '中标'
                elif title.find('成交') >= 0:
                    category = '成交'
                elif title.find('结果') >= 0:
                    category = '结果'
                elif title.find('单一') >= 0:
                    category = '单一'
                item = ztbkItem()
                item['title'] = title
                item['content'] = "".join(response.xpath('//div[@class="news-infodetail-para"]').extract())
                item['source'] = '辽宁省公共资源交易服务平台'
                item['category'] = category
                item['type'] = ''
                item['region'] = '辽宁省'
                item['time'] = kwargs['time'].strip()
                item['website'] = '辽宁省公共资源交易服务平台'
                item['module_name'] = '辽宁省-公共交易平台'
                item['spider_name'] = 'liaoning_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="news-infodetail-para"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@class="news-infodetail-para"]//a[contains(@href,"pdf") and contains(@href,"word") and contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@class="news-infodetail-para"]//a[contains(@href,"pdf") and contains(@href,"word") and contains(@href,"xls")]/@href').extract())
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