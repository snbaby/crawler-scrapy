# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from cnki_sbk_renyuan.items import  cnki_sbk_renyuanItem
from scrapy_splash import SplashRequest


class SbkRenyuanSpider(scrapy.Spider):
    name = 'sbk_renyuan'
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
        # 网站最大支持爬取300页内容
        for i in range(1, 2+1):
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
        for record in response.css(".GridTableContent tr:not(.GTContentTitle)"):
            debug=record.css("td.author_flag a.KnowledgeNetLink")
            tmp_url = "http://kns.cnki.net" + record.css("td.author_flag a.KnowledgeNetLink::attr(href)").get("")
            import urllib.parse as urlparse
            from urllib.parse import parse_qs
            tmp_url_parsed = urlparse.urlparse(tmp_url)

            talent_url = "http://kns.cnki.net/kcms/detail/knetsearch.aspx?dbcode=CDFD&sfield=au&skey=&code="
            talent_url = "http://kns.cnki.net" + talent_url
            talent_url.replace("skey=", "skey="+parse_qs(tmp_url_parsed.query)['skey'][0])
            talent_url.replace("code=", "code="+parse_qs(tmp_url_parsed.query)['scode'][0])

            item  = {}
            item['name'] = record.css("td.author_flag a::text").extract_first().strip()
            item['organization'] = record.css("td:nth-child(4) a::text").extract_first().strip()
            item['website'] = "中国知网-博硕士"
            item['link'] = talent_url
            item['spider_name'] = self.name
            item['module_name'] = '中国知网-硕博库'

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
            break
    def get_attention(self, response):
        logging.info(response.text)
        info = response.css("div.listcont ul.col8 li a::text").extract()
        logging.info("info="+ json.dumps(info))

    def parse_end(self, response, **kwargs):
        self.get_attention(response)

        sbkItem = cnki_sbk_renyuanItem()
        sbkItem['name'] = kwargs['name']
        sbkItem['organization'] = kwargs['organization']
        sbkItem['subject'] = response.css("div.baseInfo div.info p.doma::text").get("")
        sbkItem['attention_territory'] = response.css("")
        sbkItem['website'] = kwargs['website']
        sbkItem['link'] = kwargs['link']
        sbkItem['spider_name'] = kwargs['spider_name']
        sbkItem['module_name'] = kwargs['module_name']

        yield sbkItem

