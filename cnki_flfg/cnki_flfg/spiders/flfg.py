# -*- coding: utf-8 -*-
import scrapy
import logging

from cnki_flfg.items import cnki_flfgItem
from scrapy_splash import SplashRequest


class FlfgSpider(scrapy.Spider):
    name = 'flfg'
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
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
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
            splash:wait(5)
            splash:runjs("iframe = function(){ var f = document.getElementById('iframeResult'); return f.contentDocument.getElementsByTagName('body')[0].innerHTML;}")
            splash:wait(5)
            return {
                html = splash:evaljs("iframe()")
            }
        end
        """

        try:
            url = "http://law1.cnki.net/law/brief/result.aspx?dbPrefix=CLKLP"
            yield SplashRequest(url,
                                endpoint='execute',
                                args={
                                    'lua_source': script,
                                    'wait': 1,
                                    'url': url,
                                    'iframes': 1,
                                },
                                callback=self.parse_result,
                                meta={'url': url})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_result(self, response):
        page_script = """
            function main(splash, args)
                assert(splash:go(args.url))
                assert(splash:wait(1))
                splash:runjs("document.querySelector('#btnSearch').click();")
                splash:wait(5)
                splash:runjs(args.page_js)
                splash:wait(5)
                splash:runjs("document.querySelector('#iframeResult').contentDocument.getElementsByTagName('a')[30].click()")
                splash:wait(5)
                splash:runjs("iframe = function(){ var f = document.getElementById('iframeResult'); return f.contentDocument.getElementsByTagName('body')[0].innerHTML;}")
                splash:wait(5)
                return {
                    html = splash:evaljs("iframe()")
                }
            end
            """
        page_num = self.parse_pagenum(response)
        # 网站最大支持爬取300页内容
        for i in range(page_num):
            page_js = "document.querySelector('#iframeResult').contentDocument.getElementsByName('curpage2')[0].value = " + str(
                i + 1)
            yield SplashRequest(response.meta['url'],
                                endpoint='execute',
                                args={
                                    'lua_source': page_script,
                                    'wait': 1,
                                    'page_js': page_js,
                                    'url': response.meta['url'],
                                    'iframes': 1,
            },
                session_id="foo",
                callback=self.parse)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                result_cnt = response.css(
                    "input[name=lastpage]::attr(value)").extract_first()
                return int(result_cnt)
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for record in response.css(
                ".GridTableContent > tbody > tr:not(.GTContentTitle)"):
            title = record.css('td:nth-child(2) a::text').extract_first()
            pub_org = record.css('td:nth-child(3)::text').extract_first()
            pub_time = record.css('td:nth-child(4)::text').extract_first()
            timeliness = record.css('td:nth-child(5)::text').extract_first()
            url = "http://law1.cnki.net" + \
                record.css('td:nth-child(2) a::attr(href)').extract_first()
            result = {
                'title': title,
                'pub_org': pub_org,
                'pub_time': pub_time,
                'timeliness': timeliness,
                'url': url
            }
            yield scrapy.Request(url, callback=self.parse_end,
                                 dont_filter=True, meta=result)

    def parse_end(self, response):
        item = cnki_flfgItem()
        item['title'] = response.meta['title']
        item['source'] = '中国知网'
        item['pub_time'] = response.meta['pub_time']
        item['pub_org'] = response.meta['pub_org']
        item['implement_date'] = response.css(
            'div.author > p:nth-child(3)::text').extract_first().strip().replace('【实施日期】', '')
        item['pub_wordsize'] = response.css(
            'div.author > p:nth-child(4)::text').extract_first().strip().replace('【发文字号】', '')
        item['keyword'] = ''.join(
            response.css('#ChDivKeyWord *::text').extract())
        item['intro'] = response.css("#main > div:nth-child(1) > div.summary.pad10 > p:nth-child(3)::text").extract_first().strip().replace('【正文快照】', '')
        item['potency_level'] = response.css(
            '#main > div:nth-child(1) > div.summary.pad10 > p:nth-child(4)::text').extract_first().strip().replace('【效力级别】', '')
        item['timeliness'] = response.meta['timeliness']
        item['website'] = '中国知网'
        logging.info('url====' + str(response.meta['url']))
        item['link'] = response.meta['url']
        item['spider_name'] = 'flfg'
        item['module_name'] = '中国知网-法律法规'
        yield item
