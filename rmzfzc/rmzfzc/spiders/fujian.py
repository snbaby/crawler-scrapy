# -*- coding: utf-8 -*-
import scrapy

import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
import json
script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class FujianSpider(scrapy.Spider):
    name = 'fujian'
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'zcwj',  # 政策文件
                    'url': 'http://www.fujian.gov.cn/was5/web/search?channelid=291575&sortfield=-docreltime&classsql=chnlid%3D22179&prepage=15'
                },
                {
                    'topic': 'szfwj',  # 省政府文件
                    'url': 'http://www.fujian.gov.cn/was5/web/search?channelid=291575&sortfield=-docreltime&classsql=chnlid%3D22118&prepage=15'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                url = response.meta['url'] + '&page=' + str(pagenum + 1)
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                str = ''
                for text in response.css('body::text').extract():
                    str = str + text.strip()
                return int(json.loads(str)['pagenum'])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        str = ''
        for text in response.css('body::text').extract():
            str = str + text.strip()
        res = json.loads(str)
        for doc in res['docs']:
            try:
                if 'pubtime' in doc:
                    url = doc['url']
                    title = doc['title']
                    time = doc['pubtime']
                    source = doc['src']
                    article_num = doc['fileno']
                    result = {
                        'url': url,
                        'title': title,
                        'time': time,
                        'source': source,
                        'article_num':article_num
                    }
                    yield scrapy.Request(url, callback=self.parse_item, meta=result, dont_filter=True)
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
            item['title'] = response.meta['title']
            item['article_num'] = response.meta['article_num']
            item['content'] = response.css('.htmlcon').extract_first()
            item['appendix'] = appendix
            item['source'] = response.meta['source']
            item['time'] = response.meta['time']
            item['province'] = '福建省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '福建省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = "".join(response.css('.htmlcon *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '福建省人民政府'
            item['spider_name'] = 'fujian'
            item['time'] = get_times(item['time'])
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item