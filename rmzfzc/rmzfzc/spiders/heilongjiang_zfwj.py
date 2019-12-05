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
    name = 'heilongjiang_zfwj'
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
            url = "http://www.hlj.gov.cn/gkml/ztfl.html?p=1&c=1&k=&t="
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            # 在解析翻页数之前，首先解析首页内容
            for pagenum in range(page_count):
                if pagenum>0:
                    url = "http://www.hlj.gov.cn/gkml/ztfl.html?p=2&c=" + \
                      str(pagenum) + "&k=&t=" if pagenum > 1 else "http://www.hlj.gov.cn/gkml/ztfl.html?p=2&c=1&k=&t="
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        print(response.text)
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                self.add_pagenum = int(response.xpath('//*[@id="3bb45f8814654e33ae014e740ccf771b"]/div[2]/table[2]/tbody/tr[2]/td/div[2]/span/b[3]').re(r'([1-9]\d*\.?\d*)')[0])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//table[@class="xxgkzclbtab3"]/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[4]/text()').extract_first()
                item['article_num'] = selector.xpath('./td[3]/text()').extract_first()
                href = selector.xpath('./td[2]/a/@href').extract_first()
                url = response.urljoin(href)
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response, **kwargs):
        print(response)
        try:
            item = rmzfzcItem()
            item['title'] = kwargs['title']
            item['article_num'] = kwargs['article_num']
            item['content'] = "".join(response.xpath('//div[@id="zoom"]').extract())
            item['source'] = ''
            item['time'] = kwargs['time']
            item['province'] = '黑龙江省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '黑龙江省人民政府'
            item['module_name'] = '黑龙江省人民政府-政府文件'
            item['spider_name'] = 'heilongjiang_zfwj'
            item['txt'] = "".join(response.xpath('//div[@id="zoom"]//text()').extract())
            item['appendix_name'] = ";".join(response.xpath('//div[@id="zoom"]//a[contains(@href,"pdf") or contains(@href,"word") or contains(@href,"xls")]/text()').extract())
            item['link'] = response.request.url
            item['appendix'] = ";".join(response.xpath('//div[@id="zoom"]//a[contains(@href,"pdf") or contains(@href,"word") or contains(@href,"xls")]/@href').extract())
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
