# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
import datetime
import json
from utils.tools.attachment import get_attachments, get_times

url = 'http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp'
end = datetime.date.today()
begin = end.replace(day=end.day - 9)
TIMEBEGIN_SHOW = begin.strftime("%Y-%m-%d")
TIMEBEGIN = TIMEBEGIN_SHOW
TIMEEND_SHOW = end.strftime("%Y-%m-%d")
TIMEEND = TIMEEND_SHOW
data = {
    "TIMEBEGIN_SHOW": TIMEBEGIN_SHOW,
    "TIMEEND_SHOW": TIMEEND_SHOW,
    "TIMEBEGIN": TIMEBEGIN,
    "TIMEEND": TIMEEND,
    "SOURCE_TYPE": "1",
    "DEAL_TIME": "05",
    "DEAL_CLASSIFY": "00",
    "DEAL_STAGE": "0000",
    "DEAL_PROVINCE": "0",
    "DEAL_CITY": "0",
    "DEAL_PLATFORM": "0",
    "BID_PLATFORM": "0",
    "DEAL_TRADE": "0",
    "isShowAll": "1",
    "PAGENUMBER": "1"
}


class GansuSpider(scrapy.Spider):
    name = 'quanguo_ggjypt'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'SPLASH_URL': "http://47.57.108.128:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            yield scrapy.FormRequest(url=url, formdata=data, method='POST',
                                     headers={
                                         'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                         'Accept': '*/*'
                                     },
                                     callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            result = json.loads(response.text)
            page_count = result['ttlpage']
            for pagenum in range(page_count):
                data['PAGENUMBER'] = str(pagenum + 1)
                yield scrapy.FormRequest(url=url, formdata=data, method='POST',
                                         headers={
                                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                             'Accept': '*/*'
                                         },
                                         callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for tempData in json.loads(response.text)['data']:
            try:
                item = {}
                item['title'] = tempData['title']
                item['time'] = tempData['timeShow']
                item['url'] = tempData['url'].replace('/html/a', '/html/b')
                item['source'] = tempData['platformName']
                item['region'] = tempData['districtShow']
                item['type'] = tempData['stageShow']
                yield scrapy.Request(item['url'], callback=self.parse_item, meta=item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        if response.meta['title']:
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
                item['content'] = "".join(response.css('#mycontent').extract())
                item['source'] = response.meta['source']
                item['category'] = category
                item['type'] = response.meta['type']
                item['region'] = response.meta['region']
                item['time'] = response.meta['time']
                item['website'] = '全国公共资源交易服务平台'
                item['module_name'] = '全国-公共交易平台'
                item['spider_name'] = 'quanguo_ggjypt'
                item['txt'] = "".join(response.css('#mycontent *::text').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.meta['url']
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
