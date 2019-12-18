# -*- coding: utf-8 -*-
import scrapy
import logging
import time

from scrapy_splash import SplashRequest
from zpks.items import zpksItem

class QinghaiGgjyptSpider(scrapy.Spider):
    name = 'zpks_lgw'
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
        #'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
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
          wait_for_element(splash, "a.position_link")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            yield SplashRequest('https://www.lagou.com/jobs/list_?labelWords=&fromSearch=true&suginput=',
                endpoint='execute',
                args={
                    'lua_source': script,
                    'wait': 1,
                    'url': 'https://www.lagou.com/jobs/list_?labelWords=&fromSearch=true&suginput=',
                }, callback=self.parse_page)

        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
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

          assert(splash:go(args.url))
          wait_for_element(splash, "a.position_link")
          splash:runjs("document.querySelector('.item_con_list').innerHTML = ''")
          splash:runjs("document.querySelector('.pager_is_current').classList.add('test')")
          splash:runjs("document.querySelector('.pager_is_current').classList.remove('pager_is_current')")
          js = string.format("document.querySelector('.test').setAttribute('data-page-index',%d)", args.pagenum)
          splash:evaljs(js)
          splash:runjs("document.querySelector('.test').click()")
          wait_for_element(splash, ".pager_is_current")
          wait_for_element(splash, "a.position_link")
          splash:wait(1)
          return splash:html()
        end
        """
        page_count = int(self.parse_pagenum(response))
        print(page_count)
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    yield SplashRequest('https://www.lagou.com/jobs/list_?labelWords=&fromSearch=true&suginput=',
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'pagenum': pagenum,
                            'url': 'https://www.lagou.com/jobs/list_?labelWords=&fromSearch=true&suginput=',
                        },
                        callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//span[@class="pager_not_current"][last()]/@page').extract_first()) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        print(response.xpath('//span[@class="pager_is_current"][last()]/@page').extract_first())
        for href in response.xpath('//a[@class="position_link"]/@href').extract():
            try:
                print(href)
                yield scrapy.Request(href, callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            item = zpksItem()
            temp = response.xpath('//p[@class="msg ltype"]/text()').extract()
            location = response.xpath('//p[@class="msg ltype"]/text()').extract_first()
            for dd in temp:
                if dd.find('发布')>-1:
                    times = dd.replace('发布','')

            item['job'] = response.xpath('//h1/@title').extract_first()
            item['company_name'] = response.xpath('//p[@class="cname"]/a/@title').extract_first()
            item['industry'] = ''.join(response.xpath('//p[@class="fp"]/a/text()').extract())
            item['location'] = location.replace('\xa0','') if location else ''
            item['salary'] = response.xpath('//div[@class="cn"]/strong/text()').extract_first()
            item['time'] = times.replace('\xa0','') if times else ''
            item['website'] = '前程无忧'
            item['link'] = response.request.url
            item['type'] = '2'
            item['source'] = '前程无忧'
            item['content'] = ''.join(response.xpath('//div[@class="bmsg job_msg inbox"]').extract())
            item['education'] = ''
            item['spider_name'] = 'qcwy'
            item['module_name'] = '前程无忧'
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
