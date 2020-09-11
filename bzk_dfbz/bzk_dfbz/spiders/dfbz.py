# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from bzk_dfbz.items import bzk_dfbzItem
from utils.tools.attachment import get_attachments, get_times


class DfbzSpider(scrapy.Spider):
    name = 'dfbz'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        'DOWNLOADER_MIDDLEWARES': {
            # 'scrapy_splash.SplashCookiesMiddleware': 723,
            # 'scrapy_splash.SplashMiddleware': 725,
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
        #'SPLASH_URL': "http://localhost:8050/"
        # 'SPLASH_URL': "http://121.36.103.134:8050/"
    }

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            for i in range(7):
                yield scrapy.FormRequest('http://std.sacinfo.org.cn/gnocDb/queryList', formdata={'page': str(i + 1)}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            for item in json.loads(response.text):
                url = 'http://std.sacinfo.org.cn/gnocDb/queryInfo?id=' + str(item['aesId'])
                yield scrapy.Request(url, callback=self.parse, dont_filter=True, meta={'no': str(item['no'])},
                                     priority=10)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for stdid in response.css('div[stdid]::attr(stdid)').extract():
            url = 'http://std.sacinfo.org.cn/gstdDb/queryInfo?stdId' + str(stdid)
            yield scrapy.FormRequest('http://std.sacinfo.org.cn/gstdDb/queryInfo', formdata={'stdId': str(stdid)}, meta={'url': url, 'no': response.meta['no']},
                                     callback=self.parse_item)

    def parse_item(self, response):
        data = json.loads(response.text)
        try:
            item = bzk_dfbzItem()
            item['name'] = data['cName']
            item['code'] = data['stdCode']
            item['status'] = data['stdStatus']
            item['xiazai'] = ''
            item['local'] = data['province']
            item['committees'] = data['taUnit']
            item['approvalDate'] = data['issueDate']
            item['implementationDate'] = data['actDate']
            item['sourceWebsite'] = '国家标准信息查询'
            item['ics'] = data['ics']
            item['ccs'] = data['ccs']
            item['beian'] = data['recordNo']
            item['type'] = data['stdCategory']
            item['district'] = data['province']
            item['industry_classification'] = data['tradeClassified']
            item['replace'] = data['reviseStdCodes']
            item['part_replace'] = data['partReviseStdCodes']
            item['dept_host'] = data['chargeDept']
            item['publish_no'] = data['noticeNo'] if data['noticeNo'] else response.meta['no']
            item['link'] = response.meta['url']
            item['appendix_name'] = ''
            item['spider_name'] = 'dfbz'
            item['module_name'] = '标准库-地方标准'
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
