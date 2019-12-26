# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem


class ShanxiZfcgwSpider(scrapy.Spider):
    name = 'shanxi_zfcgw'
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
          wait_for_element(splash, ".list-box td[title]")
          splash:runjs("document.querySelector('.list-box').innerHTML = ''")
          js = string.format("regionCity('%s','%s');totype('%s');", args.code,args.name,args.type)
          splash:evaljs(js)
          wait_for_element(splash, ".list-box td[title]")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'cggg',  # 采购公告
                    'url': 'http://www.ccgp-shaanxi.gov.cn/notice/list.do?noticetype=3&province='
                }
            ]
            for content in contents:
                regions = [
                    {
                        'code': '610001',
                        'name': '陕西省本级'
                    },
                    {
                        'code': '6101',
                        'name': '西安市'
                    },
                    {
                        'code': '6102',
                        'name': '铜川市'
                    },
                    {
                        'code': '6103',
                        'name': '宝鸡市'
                    },
                    {
                        'code': '6104',
                        'name': '咸阳市'
                    },
                    {
                        'code': '6105',
                        'name': '渭南市'
                    },
                    {
                        'code': '6106',
                        'name': '延安市'
                    },
                    {
                        'code': '6107',
                        'name': '汉中市'
                    },
                    {
                        'code': '6108',
                        'name': '榆林市'
                    },
                    {
                        'code': '6109',
                        'name': '安康市'
                    },
                    {
                        'code': '6110',
                        'name': '商洛市'
                    },
                    {
                        'code': '6111',
                        'name': '杨凌示范区'
                    },
                    {
                        'code': '6169',
                        'name': '西咸新区'
                    }
                ]
                types = [
                    '3', '5', '4', '6', '99', '1'
                ]
                for region in regions:
                    for type in types:
                        yield SplashRequest(content['url'],
                                            endpoint='execute',
                                            args={
                                                'lua_source': script,
                                                'wait': 1,
                                                'code': region['code'],
                                                'name': region['name'],
                                                'type': type,
                                                'url': content['url'],
                                            },
                                            callback=self.parse_page,
                                            cb_kwargs={
                                                'code': region['code'],
                                                'name': region['name'],
                                                'type': type,
                                                'url': content['url']
                                            })
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
          wait_for_element(splash, ".list-box td[title]")
          splash:runjs("document.querySelector('.list-box').innerHTML = ''")
          js = string.format("regionCity('%s','%s');totype('%s');", args.code,args.name,args.type)
          splash:evaljs(js)
          wait_for_element(splash, ".list-box td[title]")
          splash:runjs("document.querySelector('.list-box').innerHTML = ''")
          js = string.format("toPage('',%d);", args.pagenum)
          splash:evaljs(js)
          wait_for_element(splash, ".list-box td[title]")
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
                                        'code': kwargs['code'],
                                        'name': kwargs['name'],
                                        'type': kwargs['type']
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
                return int(response.css('#dateTable > div > div > ul > li:nth-last-child(3) > a::text').extract_first().strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for tr in response.css('.list-box tbody tr'):
            try:
                title = tr.css('td[title]::attr(title)').extract_first()
                url = response.urljoin(tr.css('td[title] a::attr(href)').extract_first())
                region = tr.css('td:nth-child(2)::text').extract_first().replace('[','').replace(']','')
                time = tr.css('td:nth-child(4)::text').extract_first()
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
            item['content'] = response.css('.content-inner').extract_first()
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '陕西省政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = kwargs['region']
            item['appendix_name'] = ''
            item['spider_name'] = 'shanxi_zfcgw'
            item['txt'] = ''.join(
                response.css('.content-inner *::text').extract())
            item['module_name'] = '陕西省-政府采购网'

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
