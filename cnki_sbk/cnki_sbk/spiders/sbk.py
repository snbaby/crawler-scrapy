# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from cnki_sbk.items import  cnki_sbkItem
from scrapy_splash import SplashRequest


class SbkSpider(scrapy.Spider):
    name = 'sbk'
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
        script = """
        function main(splash, args)
            assert(splash:go(args.url))
            assert(splash:wait(1))
            splash:runjs("document.querySelector('#btnSearch').click();")
            splash:runjs("iframe = function(){ var f = document.getElementById('iframeResult'); return f.contentDocument.getElementsByTagName('body')[0].innerHTML;}")
            splash:wait(5)
            return splash:evaljs("iframe()")
        end
        """

        try:
            url = "http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CDMD"
            # json_body = {
            #     'js_source': "document.querySelector('#btnSearch').click();",
            #     'url': url,
            #     'console': 1,
            #     'iframes': 1,
            #     'png': 1,
            #     'html': 1,
            #     'wait': 3
            # }
            # yield scrapy.Request("http://47.106.239.73:8050/render.json",
            #                      method='POST',
            #                      headers={'Content-Type': 'application/json'},
            #                      body=json.dumps(json_body),
            #                      callback=self.parse_result)
            yield SplashRequest(url,
                                endpoint='execute',
                                args={
                                    'lua_source': script,
                                    'wait': 1,
                                    'url': url,
                                    'iframes':1,
                                },
                                callback=self.parse_result)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_result(self, response):
        logging.info("result============{}".format(response.text))

    def parse_page(self, response, **kwargs):
        page_count = self.parse_pagenum(response, kwargs)
        try:
            for content in contents:
                for pagenum in range(page_count):
                    data = {
                        "total": 0,
                        "per_page": 20,
                        "page": pagenum + 1,
                        "type": 1,
                        "scope": "",
                        "sub_scope": "",
                        "round": [],
                        "valuation": [],
                        "valuations": "",
                        "ipo_platform": "",
                        "equity_ratio": "",
                        "status": "",
                        "prov": "",
                        "city": [],
                        "time": [],
                        "selected": "",
                        "location": "",
                        "hot_city": "",
                        "currency": [],
                        "keyword": ""}
                    yield scrapy.FormRequest(content['url'], cb_kwargs=content, body=json.dumps(data), method='POST', headers=header, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        investevents = json.loads(response.text)['data']['data']
        for investevent in investevents:
            try:
                item = cnki_sbkItems()
                item['title'] = investevent['invse_title']
                item['financers'] = investevent['name']
                investors = ''
                for investor in investevent['investor']:
                    investors = investors + investor['name'] + ','
                item['investors'] = investors
                item['amount'] = investevent['money']
                item['rotation'] = investevent['round']
                item['time'] = str(investevent['year'])+'-'+str(investevent['month'])+'-'+str(investevent['day'])
                item['industry'] = investevent['com_scope']
                item['introduction'] = investevent['com_des']
                item['website'] = 'IT桔子'
                item['link'] = 'https://www.itjuzi.com/investevent/'+str(investevent['id'])
                item['content'] = investevent['invse_des']
                item['spider_name'] = 'rz'
                item['module_name'] = 'IT桔子-融资'
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
