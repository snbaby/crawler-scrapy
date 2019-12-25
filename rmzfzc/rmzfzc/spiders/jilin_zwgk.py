# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
import time
from utils.tools.attachment import get_attachments,get_times
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
  assert(splash:wait(0.1))
  wait_for_element(splash, "#content > tr > td")
  js = string.format("document.querySelector('#jump').value =%s", args.page)
  splash:evaljs(js)
  assert(splash:wait(0.1))
  splash:runjs("document.querySelector('.tmptabel').innerHTML = ''")
  assert(splash:wait(0.1))
  splash:runjs("document.querySelector('.go-button').click()")
  assert(splash:wait(0.1))
  wait_for_element(splash, ".tmptabel > tbody > tr > td")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'jilin_zwgk'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
        'DOWNLOADER_MIDDLEWARES' : {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES' : {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE' : 'scrapy_splash.SplashAwareFSCacheStorage',
        # 'SPIDER_MIDDLEWARES': {
        #     'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        # },
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
        #     'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
        #     'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
        # },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        # 'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'url': 'http://xxgk.jl.gov.cn/'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint = 'execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': 2,
                                        'url': content['url'],
                                    },
                                    callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(response.xpath('//*[@id="page-body"]/a[last()-1]/@data-page').extract_first()) + 1
        try:
            for pagenum in range(page_count):
                if pagenum > 1:
                    time.sleep(1)
                    yield SplashRequest(kwargs['url'],
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'page': pagenum,
                            'url': kwargs['url']
                        },
                        callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//*[@class="zly_xxmu_20170104ulbg2"]'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/div/a/text()').extract_first().strip()
                item['time'] = selector.xpath('./td[5]/text()').extract_first().strip()
                item['article_num'] = selector.xpath('./td[3]/text()').extract_first().strip()
                href = selector.xpath('./td[2]/div/a/@href').extract_first()
                yield scrapy.Request(href,callback=self.parse_item,dont_filter=True,cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = kwargs['title']
            item['article_num'] =  kwargs['article_num']
            item['time'] = kwargs['time']
            item['content'] = "".join(response.xpath('//div[@class="Custom_UnionStyle"]').extract())
            item['source'] = ''
            item['province'] = '吉林省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '吉林省人民政府'
            item['module_name'] = '吉林省人民政府-政务公开'
            item['spider_name'] = 'jilin_zwgk'
            item['txt'] = "".join(response.xpath('//div[@class="Custom_UnionStyle"]//text()').extract())
            item['appendix_name'] = appendix_name
            item['link'] = response.request.url
            item['appendix'] = appendix
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
