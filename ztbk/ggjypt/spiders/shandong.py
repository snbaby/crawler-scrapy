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


class shandongSzfwjSpider(scrapy.Spider):
    name = 'shandong_ggjypt'
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
            url = "http://ggzyjyzx.shandong.gov.cn/003/moreinfo.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        for href in response.xpath('//*[@class="wb-tree-item "]/a/@href'):
            try:
                url = href.extract()
                print(url)
                yield SplashRequest(url,callback=self.parse_page, dont_filter=True,cb_kwargs={'url':url})

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        print('page_count'+kwargs['url'])
        print('url'+str(page_count))
        if page_count > 0:
            page_count = page_count + 1
            try:
                for pagenum in range(page_count):
                    temUrl = kwargs['url'].replace('moreinfo.html', '')
                    url = temUrl + str(pagenum) + ".html"
                    if pagenum > 1:
                        yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
                    else:
                        yield SplashRequest(kwargs['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse,
                                            dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return int(response.xpath('//*[@class="pages-list"]/li[1]/a/text()').re(r'([1-9]\d*\.?\d*)')[2])
            if response.xpath('//div[@class="ewb-page"]/script'):
                details = response.xpath('//div[@class="ewb-page"]/script').re(r'([1-9]\d*\.?\d*)')[4]
                pageCount = response.xpath('//div[@class="ewb-page"]/script').re(r'([1-9]\d*\.?\d*)')[3]
                return int(details) / int(pageCount) + 1
            else:
                return 0
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//li[@class="ewb-list-node clearfix"]'):
            try:
                item = {}
                item['title'] = "".join(selector.xpath('./a//text()').extract())
                item['time'] = selector.xpath('./span/text()').extract_first()
                url = response.urljoin(selector.xpath('./a/@href').extract_first())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response,**kwargs):
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
                item['content'] = "".join(response.xpath('//div[@id="infocont"]').extract())
                item['source'] = ''
                item['category'] = category
                item['type'] = ''
                item['region'] = '山东省'
                item['time'] = kwargs['time']
                item['website'] = '山东省公共资源交易服务平台'
                item['module_name'] = '山东省-公共交易平台'
                item['spider_name'] = 'shandong_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@id="infocont"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@id="infocont"]//a[contains(@href,"pdf") and contains(@href,"word") and contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@id="infocont"]//a[contains(@href,"pdf") and contains(@href,"word") and contains(@href,"xls")]/@href').extract())
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
