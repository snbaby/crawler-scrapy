# -*- coding: utf-8 -*-
import scrapy

import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
import time
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

url = 'http://www.shandong.gov.cn/module/web/jpage/dataproxy.jsp'

class AnhuiSpider(scrapy.Spider):
    name = 'shandong'
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
                    'topic':'zcjd',
                    'data':{'col': '1','webid': '410','path': 'http://www.shandong.gov.cn/','columnid': '107868','sourceContentType': '1','unitid': '240818','webname': '山东省人民政府','permissiontype': '0'}
                }
                ,
                {
                    'topic': 'zcwj',
                    'data': {'col': '1','webid': '410','path': 'http://www.shandong.gov.cn/','columnid': '107851','sourceContentType': '1','unitid': '283644','webname': '山东省人民政府','permissiontype': '0'}
                }
            ]
            for content in contents:
                path = url + '?startrecord=1&endrecord=45&perpage=15'
                yield scrapy.FormRequest(path, formdata=content['data'],
                                         headers={
                                                    'Content-Type': 'application/x-www-form-urlencoded'
                                                  },
                                         callback=self.parse_page,meta=content,dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            total = int(self.parse_total(response))
            i = 0
            while i*45 < total:
                i = i + 1
                endrecord = i*45
                if endrecord > total:
                    endrecord = total
                startrecord = (i-1)*45 + 1
                path = url + '?startrecord='+str(startrecord)+'&endrecord='+str(endrecord)+'&perpage=15'
                yield scrapy.FormRequest(path, formdata=response.meta['data'],
                                         headers={
                                             'Content-Type': 'application/x-www-form-urlencoded'
                                         },
                                         callback=self.parse, meta=response.meta,dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        sel = scrapy.Selector(text=response.text)
        for href in sel.css('a::attr(href)').extract():
            try:
                yield scrapy.Request(href, callback=self.parse_item,
                                     dont_filter=True, meta=response.meta)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_total(self, response):
        sel = scrapy.Selector(text=response.text)
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(sel.css('totalrecord::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            if response.meta['topic'] == 'zcjd':
                item['title'] = response.css('meta[name=ArticleTitle]::attr(content)').extract_first()
                item['article_num'] = ''
                item['source'] = response.css('meta[name=contentSource]::attr(content)').extract_first()
                if response.css('meta[name=pubdate]::attr(content)'):
                    item['time'] = get_times(response.css('meta[name=pubdate]::attr(content)').extract_first())
                else:
                    item['time'] = get_times(response.css('meta[name=PubDate]::attr(content)').extract_first())
                item['content'] = "".join(response.css('.wip_art_con').extract())
                item['appendix'] = appendix
                item['province'] = '山东省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山东省人民政府'
                item['link'] = response.request.url
                item['txt'] = "".join(response.css('.wip_art_con *::text').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '山东省人民政府'
                item['spider_name'] = 'shandong_zcjd'
            else:
                item['title'] = response.css('meta[name=ArticleTitle]::attr(content)').extract_first()
                if response.css('meta[name=pubdate]::attr(content)'):
                    item['time'] = get_times(response.css('meta[name=pubdate]::attr(content)').extract_first())
                else:
                    item['time'] = get_times(response.css('meta[name=PubDate]::attr(content)').extract_first())
                if response.xpath('//div[@class="people-desc"]'):
                    article_num = response.xpath(
                        '//*[@class="people-desc"]/table/tbody/tr[3]/td[1]/text()').extract_first()
                    item['article_num'] = article_num.strip() if article_num else ''
                else:
                    item['article_num'] = ''
                item['appendix'] = appendix
                item['content'] = "".join(response.xpath('//div[@class="wip_art_conbg"]').extract())
                item['source'] = response.css('meta[name=contentSource]::attr(content)').extract_first()
                item['province'] = '山东省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山东省人民政府'
                item['link'] = response.request.url
                item['txt'] = "".join(response.xpath('//div[@class="wip_art_conbg"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '山东省人民政府'
                item['spider_name'] = 'shandong_zfwj'
                item['time'] = get_times(item['time'])

            if not response.css('meta[name=ArticleTitle]::attr(content)'):
                return
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item