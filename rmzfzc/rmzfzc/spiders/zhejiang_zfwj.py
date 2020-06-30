# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
class ZhejiangZfwjSpider(scrapy.Spider):
    name = 'zhejiang_zfwj'
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
        'SPLASH_URL': "http://47.57.108.128:8050/"}

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
          wait_for_element(splash, ".pgBtn")
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
                                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        url = 'http://www.zj.gov.cn/module/xxgk/search.jsp'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'

        }
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                data = {
                    'texttype': '0',
                    'currpage': str(pagenum+1),  # 翻页
                    'sortfield': ',compaltedate:0',
                    'infotypeId': ' C0201',
                    'jdid': ' 3096',
                    'area': ' 000014349',
                    'divid': ' div1545735',

                }
                yield scrapy.FormRequest(url, formdata=data, callback=self.parse, dont_filter=True, headers=headers)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('#div1545735 > table > tbody > tr > td > table.tb_title > tbody > tr > td:nth-child(2) > table > tbody > tr > td:nth-child(3) > a::text').extract_first().split('共')[1].split('页')[0].strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.css('a[onmouseover]::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url,callback=self.parse_item,meta={'url':url},dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = ''.join(response.css('title::text').extract()).strip()
            item['article_num'] = response.css('tr.xxgk-info-wh td::text').extract_first()
            item['content'] = ''.join(response.css('.article').extract())
            item['appendix'] = appendix
            item['source'] = response.css('meta[name=contentSource]::attr(content)').extract_first()
            item['time'] = get_times(response.css('meta[name=PubDate]::attr(content)').extract_first())
            item['province'] = '浙江省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '浙江省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('.article *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '浙江省人民政府'
            item['spider_name'] = 'zhejiang_zfwj'
            item['time'] = get_times(item['time'])
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item
