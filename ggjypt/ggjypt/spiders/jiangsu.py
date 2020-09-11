# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time
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

data = {
    "token": "",
    "pn": 0,
    "rn": 20,
    "sdt": "",
    "edt": "",
    "wd": "",
    "inc_wd": "",
    "exc_wd": "",
    "fields": "title",
    "cnum": "001",
    "sort": "{\"infodatepx\":\"0\"}",
    "ssort": "title",
    "cl": 200,
    "terminal": "",
    "condition": [],
    "time": [
        {
            "fieldName": "infodatepx",
            "startTime": "2017-01-01 00:00:00",
            "endTime": "2019-12-30 23:59:59"
        }
    ],
    "highlights": "title",
    "statistics": "",
    "unionCondition": "",
    "accuracy": "",
    "noParticiple": "1",
    "searchRange": "",
    "isBusiness": "1"
}
url = 'http://221.226.253.51/inteligentsearch/rest/inteligentSearch/getFullTextData'

class GuangdongSpider(scrapy.Spider):
    name = 'jiangsu_ggjypt'
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
        'SPLASH_URL': "http://47.57.108.128:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            yield scrapy.Request(url, body=json.dumps(data), method='POST',
                                 headers={'Content-Type': 'application/json'}, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        page_count = int(self.parse_pagenum(response))
        print(page_count)
        for n in range(page_count):
            data['pn'] = n * 20
            print(n)
            yield scrapy.Request(url, body=json.dumps(data), method='POST',
                                 headers={'Content-Type': 'application/json'}, callback=self.parse_page)
    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                jsonData = json.loads(response.text)
                return int(int(jsonData['result']['totalcount']) / 20) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_page(self, response):
        jsonData = json.loads(response.text)
        records = jsonData['result']['records']
        for record in records:
            item = {}
            item['title'] = record['title']
            item['link'] = 'http://jsggzy.jszwfw.gov.cn' + record['linkurl']
            item['time'] = record['infodateformat']
            try:
                print(item['link'])
                yield scrapy.Request('http://jsggzy.jszwfw.gov.cn' + record['linkurl'], callback=self.parse_item, dont_filter=True,meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
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
            for dd in response.xpath('//*[@class="ewb-trade-info"]//text()').extract():
                dd = dd.strip()
                if dd.find('来源') > -1:
                    source = dd.replace('来源：','')
            item['title'] = title
            item['content'] = "".join(response.xpath('//div[@class="ewb-trade-right l"]').extract())
            item['source'] = source
            item['category'] = category
            item['type'] = '2'
            item['region'] = '江苏省'
            item['time'] = response.meta['time']
            item['website'] = '江苏省公共资源交易服务平台'
            item['module_name'] = '江苏省-公共交易平台'
            item['spider_name'] = 'jiangsu_ggjypt'
            item['txt'] = "".join(response.xpath('//div[@class="ewb-trade-right l"]//text()').extract())
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

