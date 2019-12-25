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


class SichuanSpider(scrapy.Spider):
    name = 'sichuan'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
            'scrapy_splash.SplashCookiesMiddleware': 140,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
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
            contents = [
                {
                    'topic': 'zxwj',  # 最新文件
                    'url': 'http://www.sc.gov.cn/10462/10464/10684/12419/list_ft.shtml'
                },
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.sc.gov.cn/10462/10464/13298/13299/zcjd_list.shtml'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = kwargs['url']
                else:
                    url = kwargs['url'].replace(
                        '.shtml', '_' + str(pagenum + 1) + '.shtml')
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.pagination_index span::text').extract_first().replace(
                        '页', '').replace(
                        '共', '').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('#dash-table a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                if kwargs['topic'] == 'zxwj':
                    yield scrapy.Request(url, callback=self.parse_zxwj, cb_kwargs={'url': url}, dont_filter=True)
                else:
                    yield scrapy.Request(url, callback=self.parse_zcjd, cb_kwargs={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_zxwj(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('title::text').extract_first().replace(' - 四川省政府信息公开','').strip()
            if len(response.css('ucapcontent p:nth-child(1) *::text').extract()) > 0:
                item['article_num'] = response.css('ucapcontent p:nth-child(1) *::text').extract_first().strip()
            elif len(response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(4) *::text').extract()) > 0:
                item['article_num'] = response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(4) *::text').extract_first().strip()
            elif len(response.css('ucapcontent > div > strong *::text').extract()) > 0:
                item['article_num'] = response.css('ucapcontent > div > strong *::text').extract_first().strip()
            else:
                item['article_num'] = ''
            if len(response.css('ucapcontent').extract()) > 0:
                item['content'] = response.css('ucapcontent').extract_first()
                item['txt'] = ''.join(response.css('ucapcontent *::text').extract())
            elif len(response.css('.contText').extract()) > 0:
                item['content'] = response.css('.contText').extract_first()
                item['txt'] = ''.join(response.css('.contText *::text').extract())
            else:
                item['content'] = ''
                item['txt'] = ''
            item['appendix'] = appendix
            if len(response.css('#articleattribute > li:nth-child(2) *::text').extract()) > 0:
                item['source'] = response.css('#articleattribute > li:nth-child(2) *::text').extract_first().replace('来源:','').strip()
            else:
                item['source'] = ''

            if len(response.css('#articleattribute > li:nth-child(1) *::text').extract()) > 0:
                item['time'] = response.css('#articleattribute > li:nth-child(1) *::text').extract_first().strip()
            elif len(response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(2) *::text').extract()) > 0:
                item['time'] = response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(2) *::text').extract_first().strip()
            else:
                item['time'] = ''
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '四川省人民政府'
            item['link'] = kwargs['url']
            item['appendix_name'] = appendix_name
            item['module_name'] = '四川省人民政府'
            item['spider_name'] = 'sichuan'
            item['time'] = get_times(item['time'])
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item

    def parse_zcjd(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('title::text').extract_first().replace(' - 四川省政府信息公开','').strip()
            item['article_num'] = ''
            if len(response.css('ucapcontent').extract()) > 0:
                item['content'] = response.css('ucapcontent').extract_first()
                item['txt'] = ''.join(response.css('ucapcontent *::text').extract())
            elif len(response.css('.contText').extract()) > 0:
                item['content'] = response.css('.contText').extract_first()
                item['txt'] = ''.join(response.css('.contText *::text').extract())
            else:
                item['content'] = ''
                item['txt'] = ''
            item['appendix'] = appendix
            if len(response.css('#articleattribute > li:nth-child(2) *::text').extract()) > 0:
                item['source'] = response.css('#articleattribute > li:nth-child(2) *::text').extract_first().replace('来源:','').strip()
            else:
                item['source'] = ''

            if len(response.css('#articleattribute > li:nth-child(1) *::text').extract()) > 0:
                item['time'] = response.css('#articleattribute > li:nth-child(1) *::text').extract_first().strip()
            elif len(response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(2) *::text').extract()) > 0:
                item['time'] = response.css('.box[bgcolor] tr:nth-child(2) td:nth-child(2) *::text').extract_first().strip()
            else:
                item['time'] = ''
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '四川省人民政府'
            item['link'] = kwargs['url']
            item['appendix_name'] = appendix_name
            item['module_name'] = '四川省人民政府'
            item['spider_name'] = 'sichuan'
            item['time'] = get_times(item['time'])
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item
