# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class QinghaiZfcgwSpider(scrapy.Spider):
    name = 'qinghai_zfcgw'
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
            contents = [
                {
                    'topic': 'cggs',  # 采购公示
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement1/index.html',
                    'categoryCode': 'ZcyAnnouncement1',
                    # 'total': 159
                    'total': 1
                },
                {
                    'topic': 'gkzb',  # 公开招标11
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement2/index.html',
                    'categoryCode': 'ZcyAnnouncement2',
                    'total': 660
                },
                {
                    'topic': 'yqzbgg',  # 邀请招标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3009/index.html',
                    'categoryCode': 'ZcyAnnouncement3009',
                    'total': 3
                },
                {
                    'topic': 'jzxtpgg',  # 竞争性谈判公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3002/index.html',
                    'categoryCode': 'ZcyAnnouncement3002',
                    'total': 544
                },
                {
                    'topic': 'jzxcsgg',  # 竞争性磋商公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3011/index.html',
                    'categoryCode': 'ZcyAnnouncement3011',
                    'total': 660
                },
                {
                    'topic': 'xjcggg',  # 询价采购公告111
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3003/index.html',
                    'categoryCode': 'ZcyAnnouncement3003',
                    'total': 324
                },
                {
                    'topic': 'zbgg',  # 中标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement4/index.html',
                    'categoryCode': 'ZcyAnnouncement4',
                    'total': 660

                },
                {
                    'topic': 'bggg',  # 变更公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3/index.html',
                    'categoryCode': 'ZcyAnnouncement3',
                    'total': 660
                },
                {
                    'topic': 'flbgg',  # 废流标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement9999/index.html',
                    'categoryCode': 'ZcyAnnouncement9999',
                    'total': 632
                },
                {
                    'topic': 'zgysgg',  # 资格预审公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement8888/index.html',
                    'categoryCode': 'ZcyAnnouncement8888',
                    'total': 16
                },
                {
                    'topic': 'htgg',  # 合同公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement5/index.html',
                    'categoryCode': 'ZcyAnnouncement5',
                    'total': 660
                },
                {
                    'topic': 'dzmcgg',  # 电子卖场公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement8/index.html',
                    'categoryCode': 'ZcyAnnouncement8',
                    'total': 119
                }
            ]
            for content in contents:
                for pageNo in range(content['total']):
                    data = {
                        'categoryCode': content['categoryCode'],
                        'pageNo': str(pageNo + 1),
                        'pageSize': '15'
                    }
                    url = 'http://www.ccgp-qinghai.gov.cn/front/search/category'
                    yield scrapy.Request(url, body=json.dumps(data), dont_filter=True,
                                         method='POST',
                                         headers={'Content-Type': 'application/json'},
                                         callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for row in json.loads(response.text)['hits']['hits']:
            try:
                item = row['_source']
                url = 'http://www.ccgp-qinghai.gov.cn'+item['url']
                result = {
                    'url': url
                }
                yield scrapy.Request(url, callback=self.parse_item, meta=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
            result = json.loads(response.css('input[name=articleDetail]::attr(value)').extract_first())
            title = result['title']
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
            item['content'] = result['content']
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = result['publishDate']
            item['source'] = result['author']
            item['website'] = '青海省政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '青海省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'qinghai_zfcgw'
            item['txt'] = result['content']
            item['module_name'] = '青海-政府采购网'
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
