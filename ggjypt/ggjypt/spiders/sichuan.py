# -*- coding: utf-8 -*-
import scrapy
import logging
import time
import json
import math
import datetime

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times

url = 'http://ggzyjy.sc.gov.cn/WebBuilder/rest/searchindb/get'
end = datetime.date.today()
begin = end.replace(month=end.month - 3)
strDate = begin.strftime("%Y-%#m-%#d 00:00:00")
endDate = end.strftime("%Y-%#m-%#d 23:59:59")

data = {
    "fuTitle": "",
    "pageIndex": "1",
    "strDate": strDate,
    "endDate": endDate,
    "categorynum": "002",
    "jyResource": "000",
    "tradeType": "no"
}


class TianJinSzfwjSpider(scrapy.Spider):
    name = 'sichuan_ggjypt'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 2,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:

            yield scrapy.FormRequest(url=url,
                                     headers={
                                         'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                         'Accept': 'application/json, text/javascript, */*; q=0.01'
                                     },
                                     dont_filter=True,
                                     formdata=data, method='POST', callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = math.ceil(json.loads(response.text)['totalcount']/12)
        try:
            for pagenum in range(page_count):
                data['pageIndex'] = str(pagenum + 1)
                yield scrapy.FormRequest(url=url,
                                         headers={
                                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                             'Accept': 'application/json, text/javascript, */*; q=0.01'
                                         },
                                         dont_filter=True,
                                         meta=data,
                                         formdata=data, method='POST', callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for infodata in json.loads(response.text)['infodata']:
            try:
                infoid = infodata['infoid']
                infodate = infodata['infodate']
                categorynum = infodata['categorynum']
                zhuanzai = infodata['zhuanzai']
                title = infodata['title']

                item = {}
                item['title'] = title
                item['time'] = infodate
                item['zhuanzai'] = zhuanzai
                item['url'] = 'http://ggzyjy.sc.gov.cn/jyxx/' + categorynum[0:6] + '/' + categorynum + '/' + infodate[
                                                                                                             0:10].replace(
                    '-', '') + '/' + infoid + '.html'
                yield scrapy.Request(item['url'], callback=self.parse_item, dont_filter=True, meta=item)
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
                title = response.meta['title']
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
                item['content'] = "".join(response.xpath('//div[@class="clearfix"]').extract())
                item['source'] = response.meta['zhuanzai']
                item['category'] = category
                item['type'] = ''
                item['region'] = '四川省'
                item['time'] = response.meta['time'].strip()
                item['website'] = '四川省公共资源交易服务平台'
                item['module_name'] = '四川省-公共交易平台'
                item['spider_name'] = 'sichuan_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="clearfix"]//text()').extract())
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
