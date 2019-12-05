# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem

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
    name = 'shanghai_zcjd'
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
            url = "http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw41893/index.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                url = "http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw41893/index" + \
                      str(pagenum) + ".html" if pagenum > 0 else "http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw41893/index.html"
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return len(response.xpath('//*[@class="pagination pagination-centered"]/ul/li/a[contains(@title,"第")]/@href').extract())
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//ul[@class="uli14 pageList"]/li/a/@href'):
            try:
                url = response.urljoin(href.extract())
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        if response.text:
            try:
                item = rmzfzcItem()
                item['title'] = response.xpath('//div[@id="ivs_title"]/text()').extract_first()
                item['article_num'] = ''
                item['content'] = "".join(response.xpath('//div[@id="ivs_content"]').extract())
                item['source'] = '上海市人民政府'
                item['time'] = response.xpath('//div[@id="ivs_date"]/text()').extract_first().replace(')','').replace('(','')
                item['province'] = '上海市'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '上海市人民政府'
                item['module_name'] = '上海市人民政府-政策解读'
                item['spider_name'] = 'shanghai_zcjd'
                item['txt'] = "".join(response.xpath('//div[@id="ivs_content"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@id="ivs_content"]//a[contains(@href,"pdf") or contains(@href,"word") or contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@id="ivs_content"]//a[contains(@href,"pdf") or contains(@href,"word") or contains(@href,"xls")]/@href').extract())
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
