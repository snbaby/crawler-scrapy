# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
import time
from utils.tools.attachment import get_attachments,get_times
class heilongjiangZfwjSpider(scrapy.Spider):
    name = 'heilongjiang_zfwj'
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
          wait_for_element(splash, "#pages")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'zfwj',  # 交易信息列表
                    'url': 'http://www.hlj.gov.cn/gkml/ztfl.html?p=1&c=1&k=&t='
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': 40,
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
          wait_for_element(splash, "#pages")
          splash:wait(1)
          return splash:html()
        end
        """
        page_count = int(self.parse_pagenum(response)) + 1
        print(page_count)
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    url = 'http://www.hlj.gov.cn/gkml/ztfl.html?p='+str(pagenum)+'&c=1&k=&t='
                    yield SplashRequest(url,
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
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
                return response.xpath('//*[@id="pages"]/a[last()]/@href').re(r'([1-9]\d*\.?\d*)')[0]
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        script = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(1))
          return {
            html = splash:html(),
          }
        end
        """
        for selector in response.xpath('//*[@id="_fill"]/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[4]/text()').extract_first()
                item['article_num'] = selector.xpath('./td[2]/div/ul/li[6]/text()').extract_first()
                item['source'] = selector.xpath('./td[3]/text()').extract_first()
                url = selector.xpath('./td[2]/a/@href').extract_first()
                item['url'] = url
                if url:
                    print('url==='+url)
                    yield SplashRequest(url, endpoint='execute',
                                        args={'lua_source': script, 'wait': 1, 'url': url},
                                        callback=self.parse_item, dont_filter=True, meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            if response.meta['title']:
                appendix, appendix_name = get_attachments(response)
                item = rmzfzcItem()
                item['title'] = response.meta['title']
                item['article_num'] = response.meta['article_num']
                item['content'] = "".join(response.xpath('//*[@class="zwnr"]').extract())
                item['appendix'] = appendix
                item['source'] = response.meta['source']
                item['time'] = response.meta['time']
                item['province'] = '黑龙江省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '黑龙江省人民政府'
                item['module_name'] = '黑龙江省人民政府-政策解读'
                item['spider_name'] = 'heilongjiang_zfwj'
                item['txt'] = "".join(response.xpath('//*[@class="zwnr"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.meta['url']
                item['time'] = get_times(item['time'])
                print("===========================>crawled one item" +
                    response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
