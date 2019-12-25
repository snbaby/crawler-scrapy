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

url = 'http://www.nmg.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=5000&perpage=5000'


class AnhuiSpider(scrapy.Spider):
    name = 'neimenggu_zcjd'
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
                    'data':{'col': '1','appid': '1','webid': '2','path': '/','columnid': '428','sourceContentType': '1','unitid': '1239','webname': '内蒙古自治区政府门户网站','permissiontype': '0'}
                },
                {
                    'data': {'col': '1','appid': '1','webid': '2','path': '/','columnid': '429','sourceContentType': '1','unitid': '1239','webname': '内蒙古自治区政府门户网站','permissiontype': '0'}
                },
                {
                    'data': {'col': '1','appid': '1','webid': '2','path': '/','columnid': '5560','sourceContentType': '1','unitid': '1239','webname': '内蒙古自治区政府门户网站','permissiontype': '0'}
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(url, formdata=content['data'],
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                         callback=self.parse_page,cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        text = response.text.replace('<![CDATA[', '').replace(']]>','').replace(
            '<datastore>', '').replace('<nextgroup>', '').replace('<recordset>', '').replace('</recordset>','').replace('</datastore>','').replace(
            '<record>', '').replace('</nextgroup>', '')
        sel = scrapy.Selector(text=text)
        for href in sel.xpath('//*[@class="msg_listcon_list_title"]/a/@href').extract():
            try:
                yield scrapy.Request('http://www.nmg.gov.cn' + href, callback=self.parse_item,
                                     dont_filter=True, cb_kwargs=kwargs)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.xpath('//*[@class="main-fl-tit"]/text()').extract_first()
            item['article_num'] = ''
            item['content'] = "".join(response.xpath('//div[@id="zoom"]').extract())
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.xpath('//*[@class="left fbrq_01"]/text()').extract_first().replace('发布日期：','')
            item['province'] = '内蒙古自治区'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '内蒙古自治区人民政府'
            item['link'] = response.request.url
            item['txt'] = "".join(response.xpath('//div[@id="zoom"]//text()').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '内蒙古自治区人民政府'
            item['spider_name'] = 'neimenggu_zcjd'
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