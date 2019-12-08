# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem


class QinghaiGgjyptSpider(scrapy.Spider):
    name = 'qinghai_ggjypt'
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
                  wait_for_element(splash, ".active")
                  splash:wait(1)
                  return splash:html()
                end
                """
        try:
            contents = [
                {
                    'topic': 'gcjs',  # 工程建设
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001001/secondPage.html'
                },
                {
                    'topic': 'zfcg',  # 政府采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001002/secondPage.html'
                },
                {
                    'topic': 'ypcq',  # 药品采购
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001003/secondPage.html'
                },
                {
                    'topic': 'cqjy',  # 产权交易
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001004/secondPage.html'
                },
                {
                    'topic': 'kqjtd',  # 矿权及土地
                    'url': 'http://www.qhggzyjy.gov.cn/ggzy/jyxx/001005/secondPage.html'
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
                total = int(response.css('.m-pagination-info::text').extract_first().split('of')[1].replace('entires', '').strip())
                if total/10 == int(total/10):
                    return int(total/10)
                else:
                    return int(total/10) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for tr in response.css('#record tr'):
            try:
                title = tr.css(
                    'td:nth-child(2) a::attr(title)').extract_first()
                url = response.urljoin(
                    tr.css('td:nth-child(2) a::attr(href)').extract_first())
                region = tr.css(
                    'td:nth-child(3) span::attr(title)').extract_first()
                time = tr.css('td:nth-child(4) span::text').extract_first()
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time

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
            if len(response.css('.ewb-info-content')) > 0:
                item['content'] = response.css(
                    '.ewb-info-content').extract_first()
                item['txt'] = ''.join(
                    response.css('.ewb-info-content *::text').extract())
            elif len(response.css('.xiangxiyekuang')) > 0:
                item['content'] = response.css(
                    '.xiangxiyekuang').extract_first()
                item['txt'] = ''.join(
                    response.css('.xiangxiyekuang *::text').extract())
            else:
                item['content'] = ''
                item['txt'] = ''
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '青海省公共资源交易网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = kwargs['region']
            item['appendix_name'] = ''
            item['spider_name'] = 'qinghai_ggjypt'
            item['module_name'] = '青海-公共交易平台'
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
