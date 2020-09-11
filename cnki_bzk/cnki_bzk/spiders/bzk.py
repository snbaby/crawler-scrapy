# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from cnki_bzk.items import cnki_bzkItem


class SbkSpider(scrapy.Spider):
    name = 'bzk'
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
            urls = 'http://localhost:8888/getCookie?url=http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CCND'
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
            yield scrapy.Request('http://kns.cnki.net/kns/brief/result.aspx?dbprefix=CCND', callback=self.parse_page, meta=response.meta, dont_filter=True)

    def parse_page(self, response):
        for page_num in range(120):
            new_url = 'http://kns.cnki.net/kns/brief/brief.aspx?curpage=' + str(page_num+1) + '&RecordsPerPage=50&QueryID=6&ID=&turnpage=1&tpagemode=L&dbPrefix=CCND&Fields=&DisplayMode=listmode&PageName=ASP.brief_result_aspx&isinEn=0&'
            print(new_url)
            yield scrapy.Request(new_url, callback=self.parse, meta=response.meta, dont_filter=True)

    def parse(self, response):
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
            print('paper_url==' + str(paper_url))
            yield scrapy.Request(paper_url, callback=self.parse_end,headers={'type': 'item'}, meta=item, dont_filter=True)

    def parse_end(self, response):
        logging.info('url====' + str(response.meta['link']))
        try:
            item = cnki_bzkItem()
            item['title'] = response.meta['title']
            item['author'] = response.meta['author']
            item['name'] = response.meta['name']
            item['sub_title'] = ''
            item['intro'] = ''
            item['version'] = ''
            result = response.css('div.brief>div.row')
            for i in range(len(result)):
                if result[i].css('span::text').get("").strip() == '正文快照：':
                    item['intro'] = result[i].css('.abstract-text::text').get("").strip()
                if result[i].css('span::text').get("").strip() == '副标题：':
                    item['sub_title'] = result[i].css('p::text').get("").strip()
            result1 = response.css('div.doc-top>div.row')
            for i in range(len(result1)):
                if result1[i].css('span::text').get("").strip() == '版号：':
                    item['version'] = result1[i].css('p::text').get("").strip()
            item['intro'] = response.css('.abstract-text *::text').extract()
            item['date'] = response.meta['date']
            item['website'] = response.meta['website']
            item['link'] = response.meta['link']
            item['spider_name'] = response.meta['spider_name']
            item['module_name'] = response.meta['module_name']
            print('paper_url==' + str(response.url))
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
