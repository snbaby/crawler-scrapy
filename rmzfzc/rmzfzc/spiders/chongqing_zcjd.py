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


class TianJinSzfwjSpider(scrapy.Spider):
    name = 'chongqing_zcjd'
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
            url = "http://www.cq.gov.cn/zwgk/zcwjjd"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        for href in response.xpath('//div[@class="btbg"]/a/@href'):
            try:
                url1 = 'http://www.cq.gov.cn' + href.extract()
                print(url1)
                yield SplashRequest(url1,callback=self.parse_page, dont_filter=True,cb_kwargs={'url':url1})

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        url = response.xpath('//a[@class="more"]/@href').extract_first()
        url = 'http://www.cq.gov.cn' + url
        item = {'url': url}
        yield SplashRequest(url, callback=self.parse_page, dont_filter=True, cb_kwargs=item)
    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            page_count = page_count + 1
            if page_count > 0 :
                for pagenum in range(page_count):
                    temUrl = kwargs['url'] + '_'
                    url = temUrl + str(pagenum) if pagenum > 1 else kwargs['url']
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return response.xpath('//*[@class="total"]/text()').re(r'([1-9]\d*\.?\d*)')[1]
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//ul[@class="list"]/li'):
            try:
                item = {}
                item['title'] = selector.xpath('./a/text()').extract_first()
                item['time'] = selector.xpath('./span/text()').extract_first()
                url = 'http://www.cq.gov.cn' + selector.xpath('./a/@href').extract_first()
                if url:
                    yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        if kwargs['title']:
            try:
                appendix, appendix_name = get_attachments(response)
                source = response.xpath('//div[@class="fl"]/span/text()').extract_first()
                item = rmzfzcItem()
                item['title'] = kwargs['title']
                item['article_num'] = ''
                item['content'] = "".join(response.xpath('//div[@class="conTxt"]').extract())
                item['source'] = source.replace('来源：','') if source else '重庆市人民政府'
                item['time'] = kwargs['time']
                item['province'] = '重庆市'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '重庆市人民政府'
                item['module_name'] = '重庆市人民政府-市政府文件'
                item['spider_name'] = 'chongqing_zcjd'
                item['txt'] = "".join(response.xpath('//div[@class="conTxt"]//text()').extract())
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
