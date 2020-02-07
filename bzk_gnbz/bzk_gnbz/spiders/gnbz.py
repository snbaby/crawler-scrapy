# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from bzk_gnbz.items import bzk_gnbzItem
from utils.tools.attachment import get_attachments, get_times


class GnbzSpider(scrapy.Spider):
    name = 'gnbz'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

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
                    'topic': 'gnbz',  # 采购结果
                    'url': 'http://std.sacinfo.org.cn/gnoc/queryAll'
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
                  js = string.format("document.querySelector('#gblist > table > tbody > tr:nth-child(%d) > td:nth-child(3) > a').click()", args.num)
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
                    dont_filter=True,
                    meta=response.meta)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        script = """
        function main(splash, args)
          splash:go(args.url)
          splash:wait(2)
          return splash:html()
        end
        """
        try:
            item = {}
            item['name'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(2) > td:nth-child(2)::text').extract_first()
            item['code'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(1) > td:nth-child(2)::text').extract_first()
            item['status'] = ''
            item['xiazai'] = ''
            item['committees'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(12) > td:nth-child(2)::text').extract_first()
            item['approvalDate'] = get_times(response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(4) > td:nth-child(2)::text').extract_first())
            item['implementationDate'] = get_times(response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(4) > td:nth-child(4)::text').extract_first())
            item['sourceWebsite'] = '国家标准信息查询'
            item['ics'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(9) > td:nth-child(2)::text').extract_first()
            item['ccs'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(9) > td:nth-child(4)::text').extract_first()
            item['en_name'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(3) > td:nth-child(2)::text').extract_first()
            item['type'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(10) > td:nth-child(2)::text').extract_first()
            item['replace'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(5) > td:nth-child(2)::text').extract_first()
            item['caibiao'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(6) > td:nth-child(2)::text').extract_first()

            item['caibiao_name'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(7) > td:nth-child(2)::text').extract_first()

            item['caibiao_level'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(8) > td:nth-child(2)::text').extract_first()

            item['caibiao_type'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(8) > td:nth-child(4)::text').extract_first()

            item['dept_host'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(11) > td:nth-child(2)::text').extract_first()

            item['dept_pub'] = ''

            item['publish_no'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(13) > td:nth-child(2) a::text').extract_first()

            item['remark'] = ''
            item['link'] = response.css(
                '#layui-layer1 > div.layui-layer-content > div > table > tbody > tr:nth-child(1) > td:nth-child(2) > a::attr(href)').extract_first()

            item['appendix_name'] = ''
            item['spider_name'] = 'gnbz'
            item['module_name'] = '标准库-国内标准'

            yield SplashRequest(item['link'],
                                endpoint='execute',
                                args={
                                    'lua_source': script,
                                    'wait': 1,
                                    'url': item['link'],
                                },
                                callback=self.parse_end,
                                dont_filter=True,
                                meta=item)
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)

    def parse_end(self, response):
        item = bzk_gnbzItem()
        item['name'] = response.meta['name']
        item['code'] = response.meta['code']
        item['status'] = response.meta['status']
        if len(response.css(
            'body > div.repbg1 > div > div > div > div > table.tdlist > tbody > tr:nth-child(4) > td > button.btn.ck_btn.btn-sm.btn-primary::attr(data-value)').extract())>0:
            item['xiazai'] = 'http://c.gb688.cn/bzgk/gb/showGb?type=online&hcno=' + str(response.css(
                'body > div.repbg1 > div > div > div > div > table.tdlist > tbody > tr:nth-child(4) > td > button.btn.ck_btn.btn-sm.btn-primary::attr(data-value)').extract_first())
        else:
            item['xiazai'] = ''
        item['committees'] = response.meta['committees']
        item['approvalDate'] = response.meta['approvalDate']
        item['implementationDate'] = response.meta['implementationDate']
        item['sourceWebsite'] = response.meta['sourceWebsite']
        item['ics'] = response.meta['ics']
        item['ccs'] = response.meta['ccs']
        item['en_name'] = response.meta['en_name']
        item['type'] = response.meta['type']
        item['replace'] = response.meta['replace']
        item['caibiao'] = response.meta['caibiao']
        item['caibiao_name'] = response.meta['caibiao_name']
        item['caibiao_level'] = response.meta['caibiao_level']
        item['caibiao_type'] = response.meta['caibiao_type']
        item['dept_host'] = response.meta['dept_host']
        item['dept_pub'] = response.css(
            'body > div.repbg1 > div > div > div > div > div:nth-child(7) > div.col-xs-12.col-md-10.content::text').extract_first()
        item['publish_no'] = response.meta['publish_no']
        item['remark'] = response.css(
            'body > div.repbg1 > div > div > div > div > div:nth-child(8) > div.col-xs-12.col-md-10.content::text').extract_first()
        item['link'] = response.meta['link']
        item['appendix_name'] = response.meta['appendix_name']
        item['spider_name'] = response.meta['spider_name']
        item['module_name'] = response.meta['module_name']
        yield item
