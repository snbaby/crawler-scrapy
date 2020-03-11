# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
import time
from utils.tools.attachment import get_attachments,get_times

class shandongZfwjSpider(scrapy.Spider):
    name = 'gansu'
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
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://localhost:8050/"}

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
          wait_for_element(splash, ".default_pgCurrentPage")
          js = string.format("document.querySelector('.default_pgCurrentPage').value =%s", args.page)
          splash:evaljs(js)
          assert(splash:wait(0.1))
          splash:runjs("document.querySelector('.default_pgContainer').innerHTML = ''")
          assert(splash:wait(0.1))
          splash:evaljs("var e = jQuery.Event('keydown');e.keyCode = 13;$('input.default_pgCurrentPage').trigger(e);")
          assert(splash:wait(0.1))
          wait_for_element(splash, ".default_pgContainer > table > tbody > tr")
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'zcwj',  # 政策文件
                    'url': 'http://www.gansu.gov.cn/col/col4729/index.html'
                },
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.gansu.gov.cn/col/col4745/index.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': 1,
                                        'url': content['url'],
                                    },
                                    callback=self.parse_page,
                                    meta=content)
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
          splash:go(args.url)
          wait_for_element(splash, ".default_pgCurrentPage")
          js = string.format("document.querySelector('.default_pgCurrentPage').value =%s", args.page)
          splash:evaljs(js)
          assert(splash:wait(0.1))
          splash:runjs("document.querySelector('.default_pgContainer').innerHTML = ''")
          assert(splash:wait(0.1))
          splash:evaljs("var e = jQuery.Event('keydown');e.keyCode = 13;$('input.default_pgCurrentPage').trigger(e);")
          assert(splash:wait(0.1))
          wait_for_element(splash, ".default_pgContainer > table > tbody > tr")
          return splash:html()
        end
        """
        page_count = int(self.parse_pagenum(response)) + 1
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    url = response.meta['url']
                    yield SplashRequest(url,
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'page': pagenum,
                            'url': url,
                        },
                        callback=self.parse,
                        meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return response.xpath('//*[@class="default_pgTotalPage"]/text()').extract_first()
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//*[@class="default_pgContainer"]/table/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[3]/span/text()').extract_first()
                url = selector.xpath('./td[2]/a/@href').extract_first()
                if url:
                    if url.startswith('/'):
                        url = 'http://www.gansu.gov.cn' + url
                    item['url'] = url
                    item['topic'] = response.meta['topic']
                    yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            if response.meta['title']:
                appendix, appendix_name = get_attachments(response)
                item = rmzfzcItem()
                item['title'] = response.meta['title']
                item['article_num'] = ''
                item['content'] = "".join(response.xpath('//*[@class="bt_content"]').extract())
                item['source'] = '省政府办公厅'
                item['time'] = response.meta['time']
                item['province'] = '甘肃省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '甘肃省人民政府'
                item['module_name'] = '甘肃省人民政府-政策解读'
                item['spider_name'] = 'gansu_' + response.meta['topic']
                item['txt'] = "".join(response.xpath('//*[@class="bt_content"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['appendix'] = appendix
                item['link'] = response.meta['url']
                item['time'] = get_times(item['time'])
                print("===========================>crawled one item" +
                    response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
