# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

from cnki_flfg.items import cnki_flfgItem
from scrapy_splash import SplashRequest


class FlfgSpider(scrapy.Spider):
    name = 'flfg'
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
            return {
                pageurl = splash:evaljs()
                html = splash:evaljs("iframe()")
            }
        end
        """

        try:
            url = "http://kns.cnki.net/kns/brief/result.aspx?dbPrefix=CLKD"
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
        base_url = "http://kns.cnki.net/kns/brief/result.aspx?dbPrefix=CLKD"
        # 网站最大支持爬取300页内容
        for i in range(1, 2 + 1):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage=' +str(i)  + '&RecordsPerPage=20&QueryID=1&ID=&turnpage=1&tpagemode=L&dbPrefix=CLKD&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
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
                result_cnt = response.css(".pagerTitleCell::text").extract_first()
                result_cnt = int(result_cnt.split()[1].replace(",", ""))
                return int((result_cnt + 19) / 20)
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
            # dest_url = http://law1.cnki.net/law/detail/detail.aspx?dbcode=CLKLP&dbname=CLKL&filename=la201912241737
            # tmp_url = /kns/detail/detail.aspx?QueryID=4&CurRec=161&dbcode=CLKLP&dbname=CLKL&filename=la201912241737
            logging.info("got record="+record.css("a.fz14::text").get())
            continue
            tmp_url = record.css(".fz14::attr(href)").get()
            tmp_url = "http://law1.cnki.net" + tmp_url
            import urllib.parse as urlparse
            from urllib.parse import parse_qs
            tmp_url_parsed = urlparse.urlparse(tmp_url)

            talent_url = "http://law1.cnki.net/law/detail/detail.aspx?"
            from urllib.parse import urlencode
            query_str = urlencode({
                'dbcode': parse_qs(tmp_url_parsed.query)['dbcode'][0],
                'dbname': parse_qs(tmp_url_parsed.query)['dbname'][0],
                'filename': parse_qs(tmp_url_parsed.query)['filename'][0],
            })
            talent_url = talent_url + query_str
            item = {}
            logging.info("tmp_url=" + tmp_url)
            logging.info("talent_url="+ talent_url)
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
        return
        sbkItem = cnki_flfgItem()
        sbkItem['title'] = response.css("span#chTitle::text").get("").strip()
        logging.info("link=" + kwargs['link'])
        return
        sbkItem['source'] = "中国法律知识资源总库法律法规库"
        sbkItem['pub_time'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > div.author > p:nth-child(2)::text").get("").strip()
        sbkItem['pub_org'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > div.author > p:nth-child(1) > a::text").get("").strip()
        sbkItem['implement_date'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > div.author > p:nth-child(3)::text").get("").strip()
        sbkItem['pub_wordsize'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > div.author > p:nth-child(4)::text").get("").strip()
        sbkItem['keyword'] = response.css("#ChDivKeyWord > a::text").get("").strip()
        sbkItem['intro'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > p:nth-child(3)::text").get("").strip()
        sbkItem['potency_level'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > p:nth-child(4)::text").get("").strip()
        sbkItem['timeliness'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > p:nth-child(5)::text").get("").strip()
        sbkItem['website'] = '中国知网-法律法规'
        sbkItem['link'] = kwargs['link']
        sbkItem['spider_name'] = self.name
        sbkItem['module_name'] = '中国知网-法律库'
        yield sbkItem

