# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem

class GuizhouZfcgwSpider(scrapy.Spider):
    name = 'guizhou_zfcgw'
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
        function main(splash, args)
          splash:go(args.url)
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'cgxqgg',  # 综合查询
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153332561072666.html?siteId=1'
                },
                {
                    'topic': 'cggg',  # 采购公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153418052184995.html?siteId=1'
                },
                {
                    'topic': 'gzgg',  # 更正公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153454200156791.html?siteId=1'
                },
                {
                    'topic': 'fbgg',  # 废标公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153488085289816.html?siteId=1'
                },
                {
                    'topic': 'zbcjgg',  # 中标(成交)公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153531755759540.html?siteId=1'
                },
                {
                    'topic': 'dylygs',  # 单一来源公示
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153567415242344.html?siteId=1'
                },
                {
                    'topic': 'dylycjgg',  # 单一来源(成交)公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153595823404526.html?siteId=1'
                },
                {
                    'topic': 'zgys',  # 资格预审
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1156071132711523.html?siteId=1'
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
                                    cb_kwargs=content,
                                    dont_filter=True)
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
          wait_for_element(splash, ".xnrx a")
          splash:runjs("document.querySelector('.xnrx').innerHTML = ''")
          js = string.format("page(%d,15,'');", args.pagenum)
          splash:evaljs(js)
          wait_for_element(splash, ".xnrx a")
          splash:wait(1)
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
                return int(response.css('.page ul li:nth-last-child(3) a::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for li in response.css('.xnrx ul li'):
            try:
                title = li.css('a::text').extract_first()
                url = response.urljoin(li.css('a::attr(href)').extract_first())
                time = li.css('span::text').extract_first()
                result = {
                    'url': url,
                    'title': title,
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
            item['content'] = response.css('#info').extract_first()
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '贵州省政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = ''
            item['appendix_name'] = ''
            item['spider_name'] = 'guizhou_zfcgw'
            item['txt'] = ''.join(response.css('#info *::text').extract())
            item['module_name'] = '贵州-政府采购网'

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