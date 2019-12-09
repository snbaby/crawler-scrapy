# -*- coding: utf-8 -*-
import scrapy
import logging
import json

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem

class QinghaiZfcgwSpider(scrapy.Spider):
    name = 'qinghai_zfcgw'
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
              return splash:html()
            end
            """
        try:
            contents = [
                {
                    'topic': 'cggs',  # 采购公示
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement1/index.html'
                },
                {
                    'topic': 'gkzb',  # 公开招标11
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement2/index.html'
                },
                {
                    'topic': 'yqzbgg',  # 邀请招标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3009/index.html'
                },
                {
                    'topic': 'jzxtpgg',  # 竞争性谈判公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3002/index.html'
                },
                {
                    'topic': 'jzxcsgg',  # 竞争性磋商公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3011/index.html'
                },
                {
                    'topic': 'xjcggg',  # 询价采购公告111
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3003/index.html'
                },
                {
                    'topic': 'zbgg',  # 中标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement4/index.html'
                },
                {
                    'topic': 'bggg',  # 变更公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement3/index.html'
                },
                {
                    'topic': 'flbgg',  # 废流标公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement9999/index.html'
                },
                {
                    'topic': 'zgysgg',  # 资格预审公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement8888/index.html'
                },
                {
                    'topic': 'htgg',  # 合同公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement5/index.html'
                },
                {
                    'topic': 'dzmcgg',  # 电子卖场公告
                    'url': 'http://www.ccgp-qinghai.gov.cn/ZcyAnnouncement/ZcyAnnouncement8/index.html'
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
              splash:go(args.url)
              splash:wait(1)
              splash:runjs("document.querySelector('.list-container').innerHTML = ''")
              splash:runjs("document.querySelector('.paginationjs-pages .active').classList.add('test')")
              splash:runjs("document.querySelector('.paginationjs-pages .test').classList.remove('active')")
              js = string.format("document.querySelector('.paginationjs-pages .test').setAttribute('data-num',%d)", args.pagenum)
              splash:evaljs(js)
              splash:runjs("document.querySelector('.paginationjs-pages .test').click()")
              wait_for_element(splash, ".list-container a")
              splash:wait(1)
              return splash:html()
            end
            """
        page_count = int(self.parse_pagenum(response, kwargs))
        page_count = 1
        try:
            for pagenum in range(page_count):
                url = kwargs['url']
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'pagenum': pagenum + 1,
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
                return int(response.css('.paginationjs-pages li:nth-last-child(2)::attr(data-num)').extract_first().strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('.list-container a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                result = {
                    'url': url
                }
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            result = json.loads(response.css('input[name=articleDetail]::attr(value)').extract_first())
            title = result['title']
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
            item['content'] = result['content']
            item['appendix'] = ''
            item['category'] = category
            item['time'] = result['publishDate']
            item['source'] = result['author']
            item['website'] = '青海省政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = ''
            item['appendix_name'] = ''
            item['spider_name'] = 'qinghai_zfcgw'
            item['txt'] = result['content']
            item['module_name'] = '青海-政府采购网'

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
