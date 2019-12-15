# -*- coding: utf-8 -*-
import scrapy

import logging
from utils.tools.attachment import get_attachments,get_times
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


class XinjiangSpider(scrapy.Spider):
    name = 'xinjiang'

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
            urls = [
                'http://www.xinjiang.gov.cn/xxgk/qwfb/fgwjx/index.html',
                'http://www.xinjiang.gov.cn/xxgk/zdfs/zcjd/index.html',
            ]
            for url in urls:
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                url = response.request.url.replace(
                    '.html', str(pagenum + 1) + ".html")
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css(
                        '#sub1 > div.f_page > ul > li:nth-last-child(1) a::attr(href)').extract_first().replace(
                        'index', '').replace(
                        '.html', ''))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.css('#sub1 div.list  ul  a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url,
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
            item['title'] = response.css('div.title h1::text').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('#news_content').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css('div.title div.t_left span:nth-child(2)::text').extract_first().replace('来源：','')
            item['time'] = response.css('div.title div.t_left span:nth-child(1)::text').extract_first().replace('时间：','')
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '新疆维吾尔自治区人民政府'
            item['link'] = response.request.url
            item['txt'] = ''.join(response.css('#news_content *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '新疆维吾尔自治区人民政府'
            item['spider_name'] = 'xinjiang'
            item['time'] = get_times(item['time'])
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
