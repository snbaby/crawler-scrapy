# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times

class YunnanZfcgwSpider(scrapy.Spider):
    name = 'yunnan_zfcgw'
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
                    'sign': 1,
                    'total': 9044
                },
                {
                    'sign': 4,
                    'total': 274
                },
                {
                    'sign': 3,
                    'total': 651
                },
                {
                    'sign': 5,
                    'total': 481
                },
                {
                    'sign': 2,
                    'total': 7557
                },
                {
                    'sign': 7,
                    'total': 2517
                }
            ]
            url = 'http://www.ccgp-yunnan.gov.cn/bulletin.do?method=moreListQuery'
            for content in contents:
                for pageNo in range(content['total']):
                    sign = content['sign']
                    data = {
                        "current": str(pageNo+1),
                        "rowCount": "10",
                        "searchPhrase": "",
                        "query_bulletintitle": "",
                        "query_startTime": "",
                        "query_endTime": "",
                        "query_sign": str(sign)
                    }
                    yield scrapy.FormRequest(url=url, formdata=data,meta={"sign":sign}, method='POST', dont_filter=True, callback=self.parse)

        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for row in json.loads(response.text)['rows']:
            try:
                title = row['bulletintitle']
                time = row['beginday']
                region = row['codeName']
                bulletin_id = row['bulletin_id']
                bulletinclass = row['bulletinclass']
                tabletype = row['tabletype']
                url = response.urljoin(
                    self.create_url(
                        bulletin_id,
                        bulletinclass,
                        tabletype,
                        response.meta['sign']))
                result = {
                    'title': title,
                    'time': time,
                    'region': region,
                    'url': url
                }
                yield scrapy.Request(url, callback=self.parse_item, meta=result, dont_filter=True)

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def create_url(self, bulletin_id, bulletinclass, tabletype, sign):
        if bulletin_id == "always_show1":
            return '/purchasedetail.do?method=contractList'
        elif sign == 3 or sign == 4:
            if bulletinclass is not None and "" != bulletinclass and "bxlx014" == bulletinclass:
                return "/contract.do?method=showContractDetail&bulletinclass=bxlx014&bulletin_id=" + bulletin_id
            else:
                return "/bulletin_zz.do?method=shownotice&bulletin_id=" + bulletin_id
        elif sign == 5:
            return "/bulletin_zz.do?method=showBulletin&bulletin_id=" + bulletin_id + "&sign=5"
        else:
            return "/bulletin_zz.do?method=showBulletin&bulletin_id=" + \
                bulletin_id + "&bulletinclass=" + bulletinclass

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
            item['content'] = ''.join(
                response.css('.col-xs-10-sm').extract())
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '云南政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '云南省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'yunnan_zfcgw'
            item['txt'] = ''.join(
                response.css('.col-xs-10-sm *::text').extract())
            item['module_name'] = '云南-政府采购网'
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
