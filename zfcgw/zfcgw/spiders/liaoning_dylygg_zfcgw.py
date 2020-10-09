# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
class LiaoningDylyggZfcgwSpider(scrapy.Spider):
    name = 'liaoning_dylygg_zfcgw'
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
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter'
        }

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=getPubInfoList&t_k=null'
            pageTotal = 83
            for pageCurrent in range(pageTotal):
                data = {
                    'current': str(pageCurrent + 1),
                    'rowCount': '10',
                    'searchPhrase': '',
                    'infoTypeCode': '1008',
                    'privateOrCity': '1',
                }
                yield scrapy.FormRequest(url=url, formdata=data, method='POST', dont_filter=True, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        result = json.loads(response.text)
        for row in result['rows']:
            try:
                title = row['title']
                url = row['redirectURL']
                region = row['districtName']
                time = row['releaseDate']
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time

                }
                yield scrapy.Request(url,
                                     dont_filter=True,
                                     callback=self.parse_item,
                                     meta=result)
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
            item['content'] = response.css('form').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '辽宁政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '辽宁省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'liaoning_dylygg_zfcgw'
            item['txt'] = ''.join(response.css('form *::text').extract())
            item['module_name'] = '辽宁-单一来源公告-政府采购网'
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
