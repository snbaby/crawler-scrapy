# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from bzk_dfbz.items import bzk_dfbzItem
from utils.tools.attachment import get_attachments, get_times


class DfbzSpider(scrapy.Spider):
    name = 'dfbz'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        script = """
            function main(splash, args)
              splash:go(args.url)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              splash:runjs("document.querySelector('.load-more').click()")
              splash:wait(1)
              return splash:html()
            end
            """
        try:
            contents = [
                {
                    'topic': 'dfbz',  # 采购结果
                    'url': 'http://std.sacinfo.org.cn/gnocDb/queryAll'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url': content['url'],
                },
                    callback=self.parse_page,
                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            for href in response.css('.panel-body a::attr(href)').extract():
                url = response.urljoin(href)
                yield SplashRequest(url, callback=self.parse, meta={'url': url})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        script = """
            function main(splash, args)
              splash:go(args.url)
              splash:wait(1)
              js = string.format("document.querySelector('#gblist > table > tbody > tr:nth-child(%d) > td:nth-child(4) > a').click()", args.num)
              splash:evaljs(js)
              splash:wait(2)
              return splash:html()
            end
            """
        for num in range(
                len(response.css('div[stdid]::attr(stdid)').extract())):
            try:
                yield SplashRequest(response.meta['url'],
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'num': num + 1,
                                        'url': response.meta['url'],
                },
                    callback=self.parse_item,
                    meta=response.meta)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            item = bzk_dfbzItem()
            item['name'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(4) > td:nth-child(2)::text').extract_first()
            item['code'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(3) > td:nth-child(2)::text').extract_first()
            item['status'] = ''
            item['xiazai'] = ''
            item['local'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(1) > td:nth-child(2)::text').extract_first()
            item['committees'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(11) > td:nth-child(2)::text').extract_first()
            item['approvalDate'] = get_times(response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(5) > td:nth-child(2)::text').extract_first())
            item['implementationDate'] = get_times(response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(5) > td:nth-child(4)::text').extract_first())
            item['sourceWebsite'] = '国家标准信息查询'
            item['ics'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(10) > td:nth-child(2)::text').extract_first()
            item['ccs'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(10) > td:nth-child(4)::text').extract_first()
            item['beian'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(2) > td:nth-child(2)::text').extract_first()
            item['type'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(7) > td:nth-child(2)::text').extract_first()
            item['district'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(1) > td:nth-child(2)::text').extract_first()
            item['industry_classification'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(6) > td:nth-child(2)::text').extract_first()

            item['replace'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(8) > td:nth-child(2)::text').extract_first()

            item['part_replace'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(9) > td:nth-child(2)::text').extract_first()

            item['dept_host'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(11) > td:nth-child(2)::text').extract_first()

            item['publish_no'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(13) > td:nth-child(2) a::text').extract_first()

            item['link'] = response.meta['url']
            item['appendix_name'] = ''
            item['spider_name'] = 'dfbz'
            item['module_name'] = '标准库-地方标准'

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
