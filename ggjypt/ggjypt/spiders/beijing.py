# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
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
    name = 'beijing_ggjypt'
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
            url = "https://ggzyfw.beijing.gov.cn/jylcgcjs/index.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        for href in response.xpath('//ul[@class="panel-tab"]/li/@data-href'):
            try:
                url = response.urljoin(href.extract())
                yield SplashRequest(url,callback=self.parse_more, dont_filter=True,cb_kwargs={'url':url})

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_more(self, response,**kwargs):
        if response.xpath('//ul[@class="panel-search2"]/li/a/@href'):
            for href in response.xpath('//ul[@class="panel-search2"]/li/a/@href'):
                try:
                    url = response.urljoin(href.extract())
                    yield SplashRequest(url,callback=self.parse_page, dont_filter=True,cb_kwargs={'url':url})
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        else:
            try:
                yield SplashRequest(kwargs['url'], callback=self.parse_page, dont_filter=True,
                                    cb_kwargs={'url': kwargs['url']})
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                temUrl = kwargs['url'].replace('.html', '')+'_'
                url = temUrl + \
                      str(pagenum) + ".html" if pagenum > 0 else kwargs['url']
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return int(response.xpath('//*[@class="pages-list"]/li[1]/a/text()').re(r'([1-9]\d*\.?\d*)')[2])
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//ul[@class="article-list2"]/li/a/@href'):
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
                appendix, appendix_name = get_attachments(response)
                category = '其他';
                title = response.xpath('//div[@class="lc-title"]/text()').extract_first() if response.xpath('//div[@class="lc-title"]/text()') else response.xpath('//div[@class="div-title"]/text()').extract_first()
                time = response.xpath('//div[@class="lc-title-s"]/text()').extract_first() if response.xpath('//div[@class="lc-title-s"]/text()') else response.xpath('//div[@class="div-title2"]/text()').extract_first()
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
                item['content'] = "".join(response.xpath('//div[@class="newsCon"]').extract())
                item['source'] = '北京市公共资源交易服务平台'
                item['category'] = category
                item['type'] = ''
                item['region'] = '北京市'
                item['time'] = get_times(time)
                item['website'] = '北京市公共资源交易服务平台'
                item['module_name'] = '北京市-公共交易平台'
                item['spider_name'] = 'beijing_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="newsCon"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.request.url
                item['appendix'] = appendix
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
