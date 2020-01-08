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
        """splash:runjs("document.getElementById('iframeResult').contentDocument.body.getElementsByClassName('fz14')[0].click()")
                    splash:wait(3)
                    local ret = splash:evaljs("document.body.innerHTML")"""
        page_script = """
                function main(splash, args)
                    splash:init_cookies(splash.args.cookies)
                    assert(splash:go(args.url))
                    assert(splash:wait(1))
                    splash:runjs("document.querySelector('#btnSearch').click();")
                    splash:wait(5)
                    js_string= "document.getElementById('iframeResult').src='" .. args.new_url .. "'"
                    splash:runjs(js_string)
                    splash:wait(5)
                    splash:runjs("iframe = function(){ var f = document.getElementById('iframeResult'); return f.contentDocument.getElementsByTagName('body')[0].innerHTML;}")

                    
                    local iframe_result = splash:evaljs("iframe()")
                    local entries = splash:history()
                    local last_response = entries[#entries].response
                    return {
                        cookies = splash:get_cookies(),
                        html = iframe_result,
                        headers = last_response.headers,
                    }
                end
                """
        page_num = self.parse_pagenum(response)
        base_url="http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CDMD"
        for i in range(1, 2):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage='+str(i)+'&RecordsPerPage=20&QueryID=0&ID=&turnpage=1&tpagemode=L&dbPrefix=CDMD&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
            yield SplashRequest(base_url,
                                endpoint='execute',
                                args={
                                    'lua_source': page_script,
                                    'wait': 1,
                                    'url': base_url,
                                    'new_url':new_url,
                                    'iframes': 1,
                                },
                                session_id="foo",
                                callback=self.parse)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                result_cnt = response.css(".pagerTitleCell::text").extract_first()
                result_cnt = int(result_cnt.split()[1].replace(",", ""))
                return int((result_cnt+19)/20)
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        detail_page_script = """
                function main(splash, args)
                    splash:init_cookies(splash.args.cookies)
                    assert(splash:go(args.url))
                    assert(splash:wait(1))
                    return {
                        cookies = splash:get_cookies(),
                        html = splash:html(),
                    }
                end
                """
        logging.info("result=" + response.text)
        logging.info("cookies=" + json.dumps(response.data['cookies']))
        for item in response.css(".GridTableContent tr:not(.GTContentTitle)"):
            paper_url = item.css(".fz14::attr(href)").get()
            paper_url = "http://kns.cnki.net" + paper_url
            paper_url = paper_url.replace("/kns/", "/KCMS/")
            yield SplashRequest(paper_url,
                                endpoint='execute',
                                args={
                                    'url': paper_url,
                                    'lua_source': detail_page_script,
                                    'wait': 1,
                                    'iframes': 1,
                                },
                                session_id="foo",
                                headers=response.data['headers'],
                                callback=self.parse_end)
            break

    def parse_end(self, response):
        with open('paper_detail.html', 'w+') as out:
            out.write(response.body.decode('utf-8'))

