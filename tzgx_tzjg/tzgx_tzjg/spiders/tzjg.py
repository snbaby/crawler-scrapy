# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from tzgx_tzjg.items import tzgx_tzjgItem


class TzjgSpider(scrapy.Spider):
    name = 'tzjg'
    custom_settings = {
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            data = {
                "account": "13060099652",
                "password": "111111",
                "type": "pswd"}

            header = {
                ':authority': 'www.itjuzi.com',
                ':method': 'POST',
                ':path': '/api/authorizations',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8'
            }

            contents = [
                {
                    'topic': 'authorizations',  # 投资机构
                    'url': 'https://www.itjuzi.com/api/authorizations'
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(content['url'], cb_kwargs=content, body=json.dumps(data), method='POST',
                                         headers=header,
                                         callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = self.parse_pagenum(response, kwargs)
        try:
            header = {
                ':authority': 'www.itjuzi.com',
                ':method': 'POST',
                ':path': '/api/investments',
                ':scheme': 'https',
                'content-type': 'application/json;charset=UTF-8',
                'authorization': json.loads(response.text)['data']['token']
            }

            contents = [
                {
                    'topic': 'investments',  # 融资
                    'url': 'https://www.itjuzi.com/api/investments'
                }
            ]
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "total": 0,
                        "per_page": 20,
                        "page": str(pagenum+1),
                        "type": [],
                        "scope": [],
                        "sub_scope": "",
                        "round": [],
                        "valuation": "",
                        "ipo_platform": "",
                        "equity_ratio": "",
                        "status": "",
                        "prov": "",
                        "city": [],
                        "sort": "year_count",
                        "time": [],
                        "selected": "",
                        "start_time": "",
                        "end_time": "",
                        "location": "",
                        "hot_city": "",
                        "keyword": ""}
                    yield scrapy.FormRequest(content['url'], cb_kwargs=content, body=json.dumps(data), method='POST',
                                             headers=header, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 3
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                print(investevent)
                item = tzgx_tzjgItem()
                item['name'] = investevent['name']
                item['simple_name'] = investevent['name']
                item['en_name'] =''
                item['capital_type'] = ''
                item['nature'] = ''
                for invst in investevent['invst_character']:
                    item['nature'] = item['nature'] + invst['invst_character_name']+','
                item['register_location'] = ''
                item['time'] = investevent['invst_born_year']
                item['headquarters'] = ''
                item['official_website'] = ''
                item['introduction'] = investevent['des']
                item['phone'] = ''
                item['fax'] = ''
                item['location'] = ''
                item['zip_code'] = ''
                item['website'] = 'it桔子'
                item['link'] = 'https://www.itjuzi.com/investfirm/'+str(investevent['id'])
                item['company_info'] = ''
                item['investment_field'] = ''
                for scope in investevent['scope']:
                    item['investment_field'] = item['investment_field'] + scope['scope_name']+','
                item['content'] = investevent['des']
                item['spider_name'] = 'tzjg'
                item['module_name'] = 'IT桔子-投资机构'
                url = 'https://www.itjuzi.com/api/investments/' + str(investevent['id'])
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=item, dont_filter=True)
                # yield item
                # print(
                #     "===========================>crawled one item" +
                #     response.request.url)
            except Exception as e:
                logging.error(
                    self.name +
                    " in parse_item: url=" +
                    response.request.url +
                    ", exception=" +
                    e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        print(response.text)
        try:
            investevents = json.loads(response.text)['data']
            investment_round = investevents['investment_round']
            list = []
            for name in investment_round:
                list.append(name['name'].replace('&nbsp;&nbsp;',''))
            kwargs['investment_phase'] = ';'.join(list)
            yield kwargs
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)