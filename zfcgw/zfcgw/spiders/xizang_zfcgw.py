# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem

class XizangZfcgwSpider(scrapy.Spider):
    name = 'xizang_zfcgw'
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
              wait_for_element(splash,'#news_div a')
              splash:runjs("document.querySelector('#news_div').innerHTML = ''")
              js = string.format("changePage(%d)", args.pagenum)
              splash:evaljs(js)
              wait_for_element(splash,'#news_div a')
              splash:wait(1)
              return splash:html()
            end
            """
        try:
            contents = [
                {
                    'topic': 'cggg',  # 采购公告
                    'url': 'http://www.ccgp-xizang.gov.cn/shopHome/morePolicyNews.action?categoryId=124,125'
                }
            ]
            for content in contents:
                page_count = 455
                for pagenum in range(page_count):
                    yield SplashRequest(content['url'],
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
                                            'pagenum': pagenum+1,
                                            'url': content['url'],
                                        },
                                        callback=self.parse,
                                        cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for li in response.css('#news_div ul li'):
            try:
                title = li.css('a::text').extract_first()
                time = li.css('span::text').extract_first()
                url = response.urljoin(li.css('a::attr(href)').extract_first())
                result = {
                    'title': title,
                    'time': time,
                    'url': url
                }
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            title = kwargs['title']
            if title.find('招标') >= 0:
                category = '招标'
            elif title.find('中标') >= 0:
                category = '中标'
            elif title.find('成交') >= 0:
                category = '成交'
            elif title.find('结果') >= 0:
                category = '结果'
            elif title.find('单一') >= 0:
                category = '单一'
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            item['content'] = response.css('.neirong').extract_first()
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '西藏自治区政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = ''
            item['appendix_name'] = ''
            item['spider_name'] = 'xizang_zfcgw'
            item['txt'] = ''.join(
                response.css('.neirong *::text').extract())
            item['module_name'] = '西藏-政府采购网'

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