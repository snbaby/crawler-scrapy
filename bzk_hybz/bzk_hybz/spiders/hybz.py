# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from bzk_hybz.items import bzk_hybzItem
from utils.tools.attachment import get_attachments, get_times


class HybzSpider(scrapy.Spider):
    name = 'hybz'
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        script = """
            function wait_for_element(splash, css, maxwait)
              -- Wait until a selector matches an element
              -- in the page. Return an error if waited more
              -- than maxwait seconds.
              if maxwait == nil then
                  maxwait = 10
              end
              return splash:wait_for_resume(string.format([[
                function main(splash) {
                  var selector = '%s';
                  var maxwait = %s;
                  var end = Date.now() + maxwait*1000;

                  function check() {
                    if(document.querySelector(selector)) {
                      splash.resume('Element found');
                    } else if(Date.now() >= end) {
                      var err = 'Timeout waiting for element';
                      splash.error(err + " " + selector);
                    } else {
                      setTimeout(check, 200);
                    }
                  }
                  check();
                }
              ]], css, maxwait))
            end
            function main(splash, args)
              splash:go(args.url)
              wait_for_element(splash, ".page-last a")
              return splash:html()
            end
            """
        try:
            contents = [
                {
                    'topic': 'hybz',  # 行业标准
                    'url': 'http://hbba.sacinfo.org.cn/stdList'
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
                    dont_filter=True,
                    callback=self.parse_page,
                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        script = """
            function wait_for_element(splash, css, maxwait)
              -- Wait until a selector matches an element
              -- in the page. Return an error if waited more
              -- than maxwait seconds.
              if maxwait == nil then
                  maxwait = 10
              end
              return splash:wait_for_resume(string.format([[
                function main(splash) {
                  var selector = '%s';
                  var maxwait = %s;
                  var end = Date.now() + maxwait*1000;

                  function check() {
                    if(document.querySelector(selector)) {
                      splash.resume('Element found');
                    } else if(Date.now() >= end) {
                      var err = 'Timeout waiting for element';
                      splash.error(err + " " + selector);
                    } else {
                      setTimeout(check, 200);
                    }
                  }
                  check();
                }
              ]], css, maxwait))
            end
            function main(splash, args)
              splash:go(args.url)
              splash:wait(1)
              splash:runjs("document.querySelector('#hbtable').innerHTML = ''")
              splash:runjs("document.querySelector('.page-item.active').classList.add('test')")
              splash:runjs("document.querySelector('.page-item.test').classList.remove('active')")
              js = string.format("document.querySelector('.page-item.test').innerText = %d", args.pagenum)
              splash:evaljs(js)
              splash:runjs("document.querySelector('.page-item.test').click()")
              wait_for_element(splash, "#hbtable a")
              splash:wait(1)
              return splash:html()
            end
            """
        page_count = self.parse_pagenum(response, kwargs)
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    self.parse(response)
                else:
                    url = kwargs['url']
                    yield SplashRequest(url,
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
                                            'pagenum': pagenum + 1,
                                            'url': url,
                                        },
                                        dont_filter=True,
                                        callback=self.parse,
                                        cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('.page-last a::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for tr in response.css('#hbtable tbody tr'):
            try:
                result = {
                    'code': tr.css('td:nth-child(2)::text').extract_first(),
                    'name': tr.css('td:nth-child(3) a::text').extract_first(),
                    'industry': tr.css('td:nth-child(4)::text').extract_first(),
                    'status': tr.css('td:nth-child(5) span::text').extract_first(),
                    'approvalDate': tr.css('td:nth-child(6)::text').extract_first(),
                    'implementationDate': tr.css('td:nth-child(7)::text').extract_first(),
                    'beian': tr.css('td:nth-child(8)::text').extract_first(),
                    'url': response.urljoin(
                        tr.css('a::attr(href)').extract_first())}
                yield scrapy.Request(response.urljoin(tr.css('a::attr(href)').extract_first()), callback=self.parse_item,
                                     cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = bzk_hybzItem()
            appendix, appendix_name = get_attachments(response)
            item['name'] = kwargs['name']
            item['code'] = kwargs['code']
            item['status'] = kwargs['status']
            item['xiazai'] = appendix
            item['industryClassification'] = response.css('body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(10)::text').extract_first()
            if len(response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(6)').extract()) > 0:
                item['committees'] = response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(6)::text').extract_first()
            else:
                item['committees'] = ''
            item['approvalDate'] = kwargs['approvalDate']
            item['implementationDate'] = kwargs['implementationDate']
            item['sourceWebsite'] = '行业标准信息平台'
            if len(response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(4)').extract()) > 0:
                item['ics'] = response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(4)::text').extract_first()
            else:
                item['ics'] = ''

            if len(response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(2)').extract()) > 0:
                item['ccs'] = response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(2)::text').extract_first()
            else:
                item['ccs'] = ''
            item['beian'] = kwargs['beian']
            if len(response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(12)').extract()) > 0:
                item['type'] = response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(12)::text').extract_first()
            else:
                item['type'] = ''

            item['industry'] = kwargs['industry']
            item['replace'] = response.css('body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-left > dd:nth-child(10)::text').extract_first()
            if len(response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(8)').extract()) > 0:
                item['dept_pub'] = response.css(
                    'body > div.container.main-body > div > div > div > div.basic-info.cmn-clearfix > dl.basicInfo-block.basicInfo-right > dd:nth-child(8)::text').extract_first()
            else:
                item['dept_pub'] = ''

            item['publish_no'] = response.css('body > div.container.main-body > div > div > div > p:nth-child(9) > a::text').extract_first()

            if len(response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(12)').extract()) > 0:
                item['dept_create'] = response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(12)::text').extract_first()
            else:
                item['dept_create'] = ''

            if len(response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(14)').extract()) > 0:
                item['who_create'] = response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(14)::text').extract_first()
            else:
                item['who_create'] = ''

            if len(response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(10)').extract()) > 0:
                item['scope'] = response.css(
                    'body > div.container.main-body > div > div > div > p:nth-child(10)::text').extract_first()
            else:
                item['scope'] = ''

            item['link'] = kwargs['url']
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'hybz'
            item['module_name'] = '标准库-行业标准'
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
