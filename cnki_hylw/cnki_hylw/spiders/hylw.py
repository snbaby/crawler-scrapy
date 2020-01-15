# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from cnki_hylw.items import hylwItem
from scrapy_splash import SplashRequest


class HylwSpider(scrapy.Spider):
    name = 'hylw'
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
            url = "http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CIPD"
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
        base_url="http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CIPD"
        # 网站最大支持爬取300页内容
        for i in range(1, 300+1):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage='+str(i)+'2&RecordsPerPage=20&QueryID=0&ID=&turnpage=1&tpagemode=L&dbPrefix=CIPD&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=1&'
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
        for record in response.css(".GridTableContent tr:not(.GTContentTitle)"):
            #dest_url = http://kns.cnki.net/KCMS/detail/detail.aspx?dbcode=CPFD&dbname=CPFDTEMP&filename=DISE202001001007
            #tmp_url = /kns/detail/detail.aspx?QueryID=0&CurRec=21&DbCode=CPFD&dbname=CPFDTEMP&filename=DISE202001001023
            tmp_url = record.css(".fz14::attr(href)").get()
            tmp_url = "http://kns.cnki.net" + tmp_url
            import urllib.parse as urlparse
            from urllib.parse import parse_qs
            tmp_url_parsed = urlparse.urlparse(tmp_url)

            talent_url = "http://kns.cnki.net/KCMS/detail/detail.aspx?"
            from urllib.parse import urlencode
            query_str = urlencode({
                'dbcode': parse_qs(tmp_url_parsed.query)['DbCode'][0],
                'dbname': parse_qs(tmp_url_parsed.query)['dbname'][0],
                'filename': parse_qs(tmp_url_parsed.query)['filename'][0],
            })
            talent_url = talent_url + query_str
            item = {}
            item["link"] = talent_url
            yield SplashRequest(talent_url,
                                endpoint='execute',
                                args={
                                    'url': talent_url,
                                    'lua_source': detail_page_script,
                                    'wait': 1,
                                    'iframes': 1,
                                },
                                session_id="foo",
                                headers=response.data['headers'],
                                callback=self.parse_end, cb_kwargs=item)

    def parse_end(self, response, **kwargs):
        sbkItem = hylwItem()
        sbkItem['title'] = response.css("#mainArea > div.wxmain > div.wxTitle > h2::text").get("").strip()
        author_list = response.css("#mainArea > div.wxmain > div.wxTitle > div.author a::text").extract()
        sbkItem['author'] = ' '.join([str(elem) for elem in author_list])
        sbkItem['organization'] = response.css("#mainArea > div.wxmain > div.wxTitle > div.orgn > span > a::text").get("").strip()
        sbkItem['name'] = response.xpath("//label[@id='catalog_HY_NAME']/../text()").get("").strip()
        sbkItem['time'] = response.xpath("//label[@id='catalog_DATE']/../text()").get("").strip()
        sbkItem['intro'] = response.css("#ChDivSummary::text").get("").strip()
        sbkItem['address'] =  response.xpath("//label[@id='catalog_ADDR']/../text()").get("").strip()
        sbkItem['type'] = response.xpath("//label[@id='catalog_ZTCLS']/../text()").get("").strip()
        sbkItem['website'] = '中国知网-会议'
        sbkItem['link'] = kwargs['link']
        sbkItem['spider_name'] = self.name
        sbkItem['module_name'] = '中国知网-会议库'
        yield sbkItem

