# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem

class ZhejiangZfwjSpider(scrapy.Spider):
    name = 'zhejiang_zfwj'
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
          wait_for_element(splash, ".btn_page")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'zfwj',  # 交易信息列表
                    'url': 'http://www.zj.gov.cn/col/col1545735/index.html'
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
          wait_for_element(splash, ".btn_page")
          js = string.format("document.querySelector('#currpage').value =%d", args.pagenum)
          splash:evaljs(js)
          splash:runjs("document.querySelector('.btn_page').click()")
          wait_for_element(splash, ".btn_page")
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
                return int(response.css('#div1545735 > table > tbody > tr > td > table.tb_title > tbody > tr > td:nth-child(1)::text').extract_first().split('录  共')[1].split('页')[0].strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('a[onmouseover]::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url,callback=self.parse_item,cb_kwargs={'url':url},dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            item['title'] = ''.join(response.css('.title::text').extract()).strip()
            item['article_num'] = response.css('.wh_content::text').extract_first()
            item['content'] = response.css('.zjszflm').extract_first()
            item['appendix'] = ''
            if len(response.css('.xxgk_top').extract()) > 0:
                item['source'] = ''.join(response.css('.xxgk_top tr:nth-child(2) td:nth-child(2)::text').extract()).strip()
                item['time'] = ''.join(response.css('.xxgk_top tr:nth-child(2) td:nth-child(4)::text').extract()).strip()
            elif len(response.css('.fgwj_xxgk_head').extract()) > 0:
                item['source'] = ''.join(response.css('.fgwj_xxgk_head tr:nth-child(2) td:nth-child(2)::text').extract()).strip()
                item['time'] = ''.join(response.css('.fgwj_xxgk_head tr:nth-child(2) td:nth-child(4)::text').extract()).strip()
            else:
                item['source'] = ''
                item['time'] = ''
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '浙江省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = "".join(response.css('.zjszflm *::text').extract())
            item['appendix_name'] = ''
            item['module_name'] = '浙江省人民政府'
            item['spider_name'] = 'zhejiang_zfwj'
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
