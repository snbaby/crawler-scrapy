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


class HubeiSpider(scrapy.Spider):
    name = 'hubei'
    custom_settings = {
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
                    'topic': 'zfwjk',  # 政府文件库
                    'url': 'http://www.hubei.gov.cn/govfile/index.shtml'
                },
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.hubei.gov.cn/zwgk/zcsd/index.shtml'
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
        print(page_count)
        page_count = 5
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = kwargs['url']
                else:
                    url = kwargs['url'].replace(
                        '.shtml', '_' + str(pagenum) + '.shtml')
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('script::text').extract()
                           [1].split(',')[0].split('(')[1])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css(
                '.news_list li a[title]::attr(href)').extract():
            try:
                url = response.urljoin(href)
                if kwargs['topic'] == 'zfwjk':
                    yield scrapy.Request(url, callback=self.parse_zfwjk, cb_kwargs={'url': url}, dont_filter=True)
                else:
                    yield scrapy.Request(url, callback=self.parse_zcjd, cb_kwargs={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_zfwjk(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css(
                '.metadata_content > div:nth-child(3) > div:nth-child(1)::text').extract()[1].strip()
            item['article_num'] = response.css(
                '.metadata_content > div:nth-child(3) > div:nth-child(2)::text').extract()[1].strip()
            item['content'] = response.css('.content_block').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css(
                '.metadata_content > div:nth-child(2) > div:nth-child(2)::text').extract()[1].strip()
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '湖北省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(
                response.css('.content_block *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '湖北省人民政府'
            item['spider_name'] = 'hubei'
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

    def parse_zcjd(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.text-center::text').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('.content_block').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css(
                '.metadata_block ul li:nth-child(2) span::text').extract_first().replace('来源：', '')
            item['time'] = response.css(
                '.metadata_block ul li:nth-child(1) span::text').extract_first().replace('发布时间：', '')
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '湖北省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(
                response.css('.content_block *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '湖北省人民政府'
            item['spider_name'] = 'hubei'
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


