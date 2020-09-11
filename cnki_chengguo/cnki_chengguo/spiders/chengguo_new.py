# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from cnki_chengguo.items import cnki_chengguoItem


class SbkSpider(scrapy.Spider):
    name = 'chengguo_new'
    custom_settings = {
        # 并发请求
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        # 下载暂停
        'DOWNLOAD_DELAY': 0.1,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
             # 自定义随机请求头
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 120,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
    }

    def __init__(self, cookie={},pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookie = cookie
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            urls = 'http://localhost:8888/getCookie?url=http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SNAD'
            # urls = 'https://kns8.cnki.net/kcms/detail/detail.aspx?dbcode=SNAD&dbname=SNAD&filename=SNAD000000002420'
            yield scrapy.Request(urls, callback=self.parse_cookie, dont_filter=True,
                                 priority=10)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_cookie(self, response):
        if len(str(response.text)) > 10:
            print('spider.cookie:' + str(response.text))
            self.cookie = json.loads(response.text)
            yield scrapy.Request('http://kns.cnki.net/kns/brief/result.aspx?dbprefix=SNAD', callback=self.parse_page, meta=response.meta, dont_filter=True)

    def parse_page(self, response):
        for page_num in range(120):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage='+str(page_num + 1)+'&RecordsPerPage=20&QueryID=0&ID=&turnpage=1&tpagemode=L&dbPrefix=SNAD&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
            yield scrapy.Request(new_url, callback=self.parse, meta=response.meta, dont_filter=True)

    def parse(self, response):
        for record in response.css(".GridTableContent tr:not(.GTContentTitle)"):
            extracted_url = record.css(".fz14::attr(href)").get()
            tmp_url = extracted_url.replace('kns', 'kcms')
            tmp_url = "https://kns8.cnki.net" + tmp_url
            import urllib.parse as urlparse
            from urllib.parse import parse_qs
            tmp_url_parsed = urlparse.urlparse(tmp_url)
            talent_url = "https://kns8.cnki.net/kcms/detail/detail.aspx?"
            from urllib.parse import urlencode
            query_str = urlencode({
                'dbcode': parse_qs(tmp_url_parsed.query)['dbcode'][0],
                'dbname': parse_qs(tmp_url_parsed.query)['dbname'][0],
                'filename': parse_qs(tmp_url_parsed.query)['filename'][0],
            })
            talent_url = talent_url + query_str
            item = {}
            item["link"] = talent_url
            print(talent_url)
            yield scrapy.Request(talent_url, callback=self.parse_end, headers={'type': 'item'}, meta=item, dont_filter=True)

    def parse_end(self, response):
        print(response.css("div.wx-tit h1::text").get())
        sbkItem = cnki_chengguoItem()
        sbkItem['name'] = response.css("div.wx-tit h1::text").get()
        sbkItem['accomplish_person'] = response.css("div.brief div.row p.funds::text").get()
        sbkItem['first_accomplish_company'] = response.css("div.brief div.row p.funds a.author::text").get()
        sbkItem['keyword'] = response.css("div.brief div.row p.funds::text").getall()[1]
        sbkItem['zt_type'] = response.css("div.brief div.row p.funds::text").getall()[2]
        sbkItem['xk_type'] = response.css("div.brief div.row p.funds::text").getall()[3]
        sbkItem['intro'] = response.css("div.brief div.row p.funds::text").getall()[4]
        sbkItem['type'] = response.css("div.brief div.row p.funds::text").getall()[5]
        sbkItem['time'] = response.css("div.brief div.row p.funds::text").getall()[7]
        sbkItem['research_time'] = ""
        sbkItem['website'] = '中国知网-成果'
        sbkItem['link'] = response.meta['link']
        sbkItem['spider_name'] = 'chengguo'
        sbkItem['module_name'] = '中国知网-成果库'
        print('paper_url==' + str(response.url))
        yield sbkItem
