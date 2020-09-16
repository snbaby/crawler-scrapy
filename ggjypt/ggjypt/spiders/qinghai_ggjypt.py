# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class QinghaiGgjyptSpider(scrapy.Spider):
    name = 'qinghai_ggjypt'
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
        'SPLASH_URL': "http://47.57.108.128:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'gcjs',  # 工程建设
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001001/secondPage.html',
                    'categoryNum': '001001',
                    'pageIndex': 12845
                },
                {
                    'topic': 'zfcg',  # 政府采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001002/secondPage.html',
                    'categoryNum': '001002',
                    'pageIndex': 8609
                },
                {
                    'topic': 'ypcq',  # 药品采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001003/secondPage.html',
                    'categoryNum': '001003',
                    'pageIndex': 12
                },
                {
                    'topic': 'cqjy',  # 产权交易
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001004/secondPage.html',
                    'categoryNum': '001004',
                    'pageIndex': 265
                },
                {
                    'topic': 'kqjtd',  # 矿权及土地
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001005/secondPage.html',
                    'categoryNum': '001005',
                    'pageIndex': 97
                }
            ]
            url = 'http://www.qhggzyjy.gov.cn/wzds/CustomSearchInfoShow.action?cmd=Custom_Search_InfoShow'
            for content in contents:
                pageIndex = content['pageIndex']
                for pageNum in range(pageIndex):
                    data = {
                        'cnum': '001;002;003;004;005;006;007;008;009;010',
                        'front': '/ggzy',
                        'area': '0',
                        'categoryNum': '001001',
                        'pageIndex': str(pageNum + 1),
                        'pageSize': '10',
                        'xiaquCode': '',
                        'titleInfo': ''
                    }
                    print(data)
                    yield scrapy.FormRequest(url=url,
                                             headers={
                                                 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                                 'Accept': 'application/json, text/javascript, */*; q=0.01'
                                             },
                                             formdata=data, method='POST', callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        datas = json.loads(json.loads(response.text)['custom'])['records']
        try:
            for data in datas:
                title = data['title']
                url = 'http://www.qhggzyjy.gov.cn'+data['linkurl']
                region = data['xiaquname']
                time = data['date']
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time

                }
                yield scrapy.Request(url, callback=self.parse_item, meta=result, dont_filter=True)
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
            if len(response.css('.ewb-info-content')) > 0:
                item['content'] = response.css(
                    '.ewb-info-content').extract_first()
                item['txt'] = ''.join(
                    response.css('.ewb-info-content *::text').extract())
            elif len(response.css('.xiangxiyekuang')) > 0:
                item['content'] = response.css(
                    '.xiangxiyekuang').extract_first()
                item['txt'] = ''.join(
                    response.css('.xiangxiyekuang *::text').extract())
            else:
                item['content'] = ''
                item['txt'] = ''
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '青海省公共资源交易网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '青海省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'qinghai_ggjypt'
            item['module_name'] = '青海-公共交易平台'
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
