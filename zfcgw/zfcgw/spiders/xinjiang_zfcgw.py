# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class XinjiangZfcgwSpider(scrapy.Spider):
    name = 'xinjiang_zfcgw'
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
                    'topic': 'cgxmgg',  # 采购项目公告
                    'categoryCode': 'ZcyAnnouncement2',
                    'pageNo': 660
                },
                {
                    'topic': 'cggs',  # 采购公示
                    'categoryCode': 'ZcyAnnouncement1',
                    'pageNo': 106
                },
                {
                    'topic': 'cgjggg',  # 采购结果公告

                    'categoryCode': 'ZcyAnnouncement4',
                    'pageNo': 660
                },
                {
                    'topic': 'cghtgg',  # 采购合同公告

                    'categoryCode': 'ZcyAnnouncement5',
                    'pageNo': 660
                },
                {
                    'topic': 'cqbggg',  # 澄清变更公告

                    'categoryCode': 'ZcyAnnouncement3',
                    'pageNo': 660
                },
                {
                    'topic': 'fbgg',  # 废标公告

                    'categoryCode': 'ZcyAnnouncement10',
                    'pageNo': 466
                },
                {
                    'topic': 'lyys',  # 履约验收

                    'categoryCode': 'ZcyAnnouncement6',
                    'pageNo': 10
                },
                {
                    'topic': 'dzmcgg',  # 电子卖场公告

                    'categoryCode': 'ZcyAnnouncement8',
                    'pageNo': 660
                },
                {
                    'topic': 'fzfcggg',  # 非政府采购公告

                    'categoryCode': 'ZcyAnnouncement9',
                    'pageNo': 30
                }
            ]
            url = 'http://www.ccgp-xinjiang.gov.cn/front/search/category'
            for content in contents:
                for pageNo in range(content['pageNo']):
                    data = {
                        "pageNo": str(pageNo + 1),
                        "pageSize": "15",
                        "categoryCode": content['categoryCode']
                    }
                    yield scrapy.Request(url, body=json.dumps(data), method='POST',
                                         dont_filter=True,
                                         headers={
                                             'Content-Type': 'application/json',
                                             'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36',
                                             'Accept': '*/*'
                                         }, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for hits in json.loads(response.text)['hits']['hits']:
            try:
                url = 'http://www.ccgp-xinjiang.gov.cn/'+hits['_source']['url']
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
            item['website'] = '新疆政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '新疆维吾尔族自治区'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'xinjiang_zfcgw'
            item['txt'] = result['content']
            item['module_name'] = '新疆-政府采购网'
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
