# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from cnki_sbk.items import cnki_sbkItem


class SbkSpider(scrapy.Spider):
    name = 'sbk'
    custom_settings = {
        # 并发请求
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        # 下载暂停
        'DOWNLOAD_DELAY': 0.1,
        'DOWNLOADER_MIDDLEWARES': {
            # 'scrapy_splash.SplashCookiesMiddleware': 723,
            # 'scrapy_splash.SplashMiddleware': 725,
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        # 'SPLASH_URL': "http://47.57.108.128:8050/"
        # 'SPLASH_URL': "http://localhost:8050/"
    }

    def __init__(self, cookie={},pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookie = cookie
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            urls = 'http://localhost:8888/getCookie?url=http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CDMD'
            # urls = 'https://kns.cnki.net/KCMS/detail/detail.aspx?dbcode=CDFD&QueryID=0&CurRec=5700&dbname=CDFDLAST2020&filename=1019640493.nh'
            yield scrapy.Request(urls, callback=self.parse_cookie, dont_filter=True,
                                 priority=10)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_cookie(self, response):
        if len(str(response.text)) > 10:
            print('spider.cookie:' + str(response.text))
            self.cookie = json.loads(response.text)
            yield scrapy.Request('http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CDMD', callback=self.parse_page, meta=response.meta, dont_filter=True)

    def parse_page(self, response):
        for page_num in range(120):
            url = 'https://kns.cnki.net/kns/brief/brief.aspx?curpage=' + str(
                page_num + 1) + '&RecordsPerPage=50&QueryID=41&ID=&turnpage=1&tpagemode=L&dbPrefix=CDMD&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
            yield scrapy.Request(url, callback=self.parse, meta=response.meta, dont_filter=True)

    def parse(self, response):
        for record in response.css(
                ".GridTableContent tr:not(.GTContentTitle)"):
            paper_url = record.css(".fz14::attr(href)").get()
            paper_url = "http://kns.cnki.net" + paper_url
            paper_url = paper_url.replace("/kns/", "/KCMS/")

            item = {}
            item['title_cn'] = record.css(".fz14::text").get()
            item['author'] = record.css(
                "td.author_flag a::text").extract_first()
            item['degree'] = record.css(
                "td:nth-child(5)::text").extract_first()
            item['degree_award_company'] = record.css(
                "td:nth-child(4) a::text").extract_first()
            item['degree_award_year'] = record.css(
                "td:nth-child(6)::text").extract_first()
            item['website'] = "中国知网-博硕士"
            item['link'] = paper_url
            item['spider_name'] = 'sbk'
            item['module_name'] = '中国知网-硕博库'
            print('paper_url==' + str(paper_url))
            yield scrapy.Request(paper_url, callback=self.parse_end,headers={'type': 'item'}, meta=item, dont_filter=True)

    def parse_end(self, response):
        sbkItem = cnki_sbkItem()
        sbkItem['title_cn'] = response.meta['title_cn']
        sbkItem['author'] = response.meta['author']
        sbkItem['degree'] = response.meta['degree']
        sbkItem['degree_award_company'] = response.meta['degree_award_company']
        sbkItem['degree_award_year'] = response.meta['degree_award_year']
        sbkItem['website'] = response.meta['website']
        sbkItem['link'] = response.meta['link']
        sbkItem['spider_name'] = response.meta['spider_name']
        sbkItem['module_name'] = response.meta['module_name']

        sbkItem['intro'] = response.css("#ChDivSummary::text").get("").strip()
        sbkItem['tutor'] = ''
        sbkItem['type'] = ''
        sbkItem['doi'] = ''
        sbkItem['fund_name'] = ''
        result = response.css("div.doc-top>div.row")
        for i in range(len(result)):
            li = result[i].css('ul>li')
            if len(li) > 0:
                for j in range(len(li)):
                    if li[j].css('span::text').get("").strip() == '分类号：':
                        sbkItem['type'] = li[j].css('p::text').get("").strip()
                    if li[j].css('span::text').get("").strip() == 'DOI：':
                        sbkItem['doi'] = li[j].css('p::text').get("").strip()
            elif result[i].css('span::text').get("").strip() == '基金资助：':
                sbkItem['fund_name'] = ''.join(result[i].css('p>a *::text').extract())
            elif result[i].css('span::text').get("").strip() == '导师：':
                sbkItem['tutor'] = result[i].css('p::text').get("").strip()
        sbkItem['keyword'] = ''.join(response.css("div.doc-top>div.brief>div.row")[1].css("p.keywords a *::text").extract())
        sbkItem['province'] = ''
        print("===========================>crawled one item")
        yield sbkItem
