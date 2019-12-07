# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

class LiaoningZfcgwSpider(scrapy.Spider):
    name = 'liaoning_zfcgw'
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
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
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
                      wait_for_element(splash, ".pagination")
                      splash:wait(1)
                      return splash:html()
                    end
                    """
        try:
            contents = [
                {
                    'topic': 'dylygg',  # 单一来源公告
                    'url': 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=goPubInfoList#'
                },
                {
                    'topic': 'jggg',  # 结果公告
                    'url': 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=goPubInfoList#'
                },
                {
                    'topic': 'cgwjgs',  # 采购文件公示
                    'url': 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=goPubInfoList#'
                },
                {
                    'topic': 'gzgg',  # 更正公告
                    'url': 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=goPubInfoList#'
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

              assert(splash:go(args.url))
              wait_for_element(splash, ".active")
              splash:runjs("document.querySelector('#record').innerHTML = ''")
              splash:runjs("document.querySelector('.active').classList.add('test')")
              splash:runjs("document.querySelector('.active').classList.remove('active')")
              splash:runjs("document.querySelector('.test').setAttribute('data-page-index',100)")
              js = string.format("document.querySelector('.test').setAttribute('data-page-index',%d)", args.pagenum)
              splash:evaljs(js)
              splash:runjs("document.querySelector('.test').click()")
              wait_for_element(splash, ".active")
              wait_for_element(splash, "#record tr")
              return splash:html()
            end
            """
        page_count = int(self.parse_pagenum(response, kwargs))
        try:
            for pagenum in range(page_count):
                url = kwargs['url']
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'pagenum': pagenum,
                                        'url': url,
                                    },
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
                return int(response.css(
                    '.m-pagination-info::text').extract_first().split('of')[1].replace('entires', '').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        pass
