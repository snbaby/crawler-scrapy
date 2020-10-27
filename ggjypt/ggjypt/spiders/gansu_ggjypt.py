# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class GansuGgjyptSpider(scrapy.Spider):
    name = 'gansu_ggjypt'
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
            url = 'http://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/getAnnoList'
            page_count = 3071
            for pagenum in range(page_count):
                data = {
                    'pageNo': str(pagenum+1),
                    'pageSize': '10',
                    'area': '620000',
                    'prjpropertynewI': 'I',
                    'prjpropertynewA': 'A',
                    'prjpropertynewD': 'D',
                    'prjpropertynewC': 'C',
                    'prjpropertynewB': 'B',
                    'prjpropertynewE': 'E',
                    'projectname': ''
                }
                yield scrapy.FormRequest(url=url, formdata=data,dont_filter=True, method='POST',
                                         headers={
                                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                             'Accept': 'text/html, */*; q=0.01',
                                             'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
                                         },
                                         callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        try:
            for selector in response.css('.sTradingInformationSelectedBtoList dl'):
                if not selector.css("::attr(id)").extract_first():
                    title = selector.css('a::attr(title)').extract_first()
                    url = response.urljoin(selector.css('a::attr(href)').extract_first())
                    time = selector.css('i::text').extract_first()
                    result = {
                        'url': url,
                        'title': title,
                        'time': time

                    }
                    yield scrapy.Request(url, callback=self.parse_item, dont_filter=True, meta=result)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
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
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            if len(response.css('#content')) > 0:
                item['content'] = response.css('#content').extract_first()
                item['txt'] = ''.join(response.css('#content *::text').extract())
            elif len(response.css('#purchaseByAnno')) > 0:
                item['content'] = response.css('#purchaseByAnno').extract_first()
                item['txt'] = ''.join(response.css('#purchaseByAnno *::text').extract())
            elif len(response.css('.jxTradingPublic')) > 0:
                item['content'] = response.css('.jxTradingPublic').extract_first()
                item['txt'] = ''.join(response.css('.jxTradingPublic *::text').extract())
            else:
                item['content'] = response.text
                item['txt'] = response.text
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '甘肃省公共资源交易网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '甘肃省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'gansu_ggjypt'
            item['module_name'] = '甘肃-公共交易平台'
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
