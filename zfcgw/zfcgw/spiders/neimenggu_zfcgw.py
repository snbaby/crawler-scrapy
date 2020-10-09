# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
class NeimengguZfcgwSpider(scrapy.Spider):
    name = 'neimenggu_zfcgw'
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
                    'topic': 'zbgg',  # 招标公告
                    'type_name': '1',
                    'total': 8529
                },
                # {
                #     'topic': 'zbgzgg',  # 招标更正公告
                #     'type_name': '2',
                #     'total': 1249
                # },
                # {
                #     'topic': 'zbcjgg',  # 中标(成交)公告
                #     'type_name': '3',
                #     'total': 7349
                # },
                # {
                #     'topic': 'zbcjgzgg',  # 中标(成交)更正公告
                #     'type_name': '4',
                #     'total': 170
                # },
                # {
                #     'topic': 'fbgg',  # 废标公告
                #     'type_name': '5',
                #     'total': 1263
                # },
                # {
                #     'topic': 'zgysgg',  # 资格预审公告
                #     'type_name': '6',
                #     'total': 2821
                # },
                # {
                #     'topic': 'zgysgzgg',  # 资格预审更正公告
                #     'type_name': '7',
                #     'total': 131
                # }
            ]
            for content in contents:
                url = 'http://www.nmgp.gov.cn/zfcgwslave/web/index.php?r=new-data%2Fanndata'
                for currentPage in range(content['total']):
                    data = {
                        'type_name': content['type_name'],
                        'annstartdate_S': '',
                        'annstartdate_E': '',
                        'byf_page': str(currentPage+1),
                        'fun': 'cggg',
                        'page_size': '18'
                    }
                    yield scrapy.FormRequest(url=url, formdata=data, method='POST', dont_filter=True, callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        try:
            for row in json.loads((response.text.encode('utf-8').decode("unicode_escape").split(',"SELECT')[0] + ']').replace('<span class="feed-time-warning">','').replace('<\/span>',''))[0]:
                title = row['TITLE']
                url = 'http://www.nmgp.gov.cn/category/cggg?tb_id='+row['ay_table_tag']+'&p_id='+row['wp_mark_id']+'&type='+row['type']
                region = row['ADNAME']
                time = row['ENDDATE'].replace('[截止：','').replace(']','').strip()
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time

                }
                yield scrapy.Request(url, callback=self.parse_item, meta=result,dont_filter=True)
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
            item['content'] = response.css('#content-box-1').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '内蒙古自治区政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '内蒙古自治区'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'neimenggu_zfcgw'
            item['txt'] = ''.join(response.css('#content-box-1 *::text').extract())
            item['module_name'] = '内蒙古自治区-政府采购网'
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
