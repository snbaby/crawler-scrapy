# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from cnki_bzk.items import cnki_bzkItem
from scrapy_splash import SplashRequest


class BzkSpider(scrapy.Spider):
    name = 'bzk'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
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
        'SPLASH_URL': "http://localhost:8050/"}

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
            url = "http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CCND"
            yield SplashRequest(url,
                                endpoint='execute',
                                args={
                                    'lua_source': script,
                                    'wait': 1,
                                    'url': url,
                                    'iframes': 1,
                                },
                                callback=self.parse_result)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_result(self, response):
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
        base_url = "http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CCND"
        # 网站最大支持爬取300页内容
        for i in range(page_num):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage=' + \
                str(i + 1) + '&RecordsPerPage=20&QueryID=6&ID=&turnpage=1&tpagemode=L&dbPrefix=CCND&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
            yield SplashRequest(base_url,
                                endpoint='execute',
                                args={
                                    'lua_source': page_script,
                                    'wait': 1,
                                    'url': base_url,
                                    'new_url': new_url,
                                    'iframes': 1,
                                },
                                session_id="foo",
                                callback=self.parse)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 300
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for record in response.css(
                ".GridTableContent tr:not(.GTContentTitle)"):
            paper_url = record.css(".fz14::attr(href)").get()
            paper_url = "http://kns.cnki.net" + paper_url
            paper_url = paper_url.replace("/kns/", "/KCMS/")
            item = {}
            item['title'] = record.css('.fz14::text').extract_first()
            item['author'] = record.css(".author_flag::text").extract_first().strip()
            item['name'] = record.css("td:nth-child(4) a::text").extract_first().strip()
            item['date'] = record.css("td:nth-child(5)::text").extract_first().strip()
            item['website'] = "中国知网-报纸库"
            item['link'] = paper_url
            item['spider_name'] = 'bzk'
            item['module_name'] = '中国知网-报纸库'

            yield scrapy.Request(paper_url, callback=self.parse_end,
                                 dont_filter=True, cb_kwargs=item)

    def parse_end(self, response, **kwargs):
        try:
            item = cnki_bzkItem()
            item['title'] = kwargs['title']
            item['author'] = kwargs['author']
            item['name'] = kwargs['name']
            result = response.css('.wxBaseinfo *::text').extract()
            item['sub_title'] = ''
            item['intro'] = ''
            item['version'] = ''
            for i in range(len(result)):
                if result[i] == '正文快照：':
                    item['intro'] = result[i+1]
                if result[i] == '副标题：':
                    item['sub_title'] = result[i+1]
                if result[i] == '版号：':
                    item['version'] = result[i+1]
            item['date'] = kwargs['date']
            item['website'] = kwargs['website']
            item['link'] = kwargs['link']
            item['spider_name'] = kwargs['spider_name']
            item['module_name'] = kwargs['module_name']
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
