# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
class LiaoningDylyggZfcgwSpider(scrapy.Spider):
    name = 'liaoning_dylygg_zfcgw'
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
          wait_for_element(splash, "#protalInfoid a[onclick]")
          splash:runjs("document.querySelector('#protalInfoid tbody').innerHTML = ''")
          splash:runjs("queryall(SYLM.DYLYGG)")
          wait_for_element(splash, "#protalInfoid a[onclick]")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'dylygg',  # 工程建设
                    'url': 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=goPubInfoList'
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
          wait_for_element(splash, "#protalInfoid a[onclick]")
          splash:runjs("document.querySelector('#protalInfoid tbody').innerHTML = ''")
          splash:runjs("queryall(SYLM.DYLYGG)")
          wait_for_element(splash, "#protalInfoid a[onclick]")
          splash:runjs("document.querySelector('#protalInfoid tbody').innerHTML = ''")
          splash:runjs("document.querySelector('#protalInfoid-footer > div > div:nth-child(1) > ul > li:nth-child(3)').classList.remove('active')")
          js = string.format("document.querySelector('#protalInfoid-footer > div > div:nth-child(1) > ul > li:nth-child(3) > a').setAttribute('data-page',%d)", args.pagenum)
          splash:evaljs(js)
          splash:runjs("document.querySelector('#protalInfoid-footer > div > div:nth-child(1) > ul > li:nth-child(3) > a').click()")
          wait_for_element(splash, "#protalInfoid a[onclick]")
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
                                        'pagenum': pagenum+1,
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
                total = int(response.css('.text-default::text').extract_first().split('共')[1].split('条')[0].strip())
                if total / 10 == int(total / 10):
                    return int(total / 10)
                else:
                    return int(total / 10) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
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
          wait_for_element(splash, "form")
          splash:wait(1)
          return splash:html()
        end
        """
        for tr in response.css('#protalInfoid tbody tr'):
            try:
                title = tr.css('td:nth-child(3)::attr(title)').extract_first()
                url = 'http://www.ccgp-liaoning.gov.cn/portalindex.do?method=getPubInfoViewOpen&infoId='+tr.css('td:nth-child(3) a::attr(onclick)').extract_first().replace('showInfo(\'','').replace('\')','')
                region = tr.css('td:nth-child(1)::attr(title)').extract_first()
                time = tr.css('td:nth-child(4)::attr(title)').extract_first()
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time

                }
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url': url,
                                    },
                                    callback=self.parse_item,
                                    cb_kwargs=result)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            appendix, appendix_name = get_attachments(response)
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
            item['content'] = response.css('form').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '辽宁政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '辽宁省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'liaoning_dylygg_zfcgw'
            item['txt'] = ''.join(response.css('form *::text').extract())
            item['module_name'] = '辽宁-单一来源公告-政府采购网'
            item['time'] = get_times(item['time'])
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
