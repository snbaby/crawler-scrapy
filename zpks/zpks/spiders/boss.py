# -*- coding: utf-8 -*-
import scrapy
import logging
import time
from scrapy_splash import SplashRequest
from zpks.items import zpksItem

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
  splash.images_enabled = false
  splash:go(args.url)
  splash:wait(1)
  return splash:html()
end
"""

class BossSpider(scrapy.Spider):
    name = 'boss'
    custom_settings = {
        'CONCURRENT_REQUESTS': 30,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
        try:
            contents = [
                {
                    'topic': 'boss',  # boss
                    'url': 'https://www.zhipin.com/c100010000/?page=1&ka=page-1'
                }
            ]
            for content in contents:
                page_count = 10
                for pagenum in range(page_count):
                    url =  'https://www.zhipin.com/c100010000/?page='+str(pagenum)+'&ka=page-'+str(pagenum)
                    yield SplashRequest(url,
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
                                            'pagenum': pagenum + 1,
                                            'url': url,
                                        },
                                        callback=self.parse,
                                        cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.xpath('//h3[@class="name"]/a/@href').extract():
            try:
                url = response.urljoin(href)
                print(url)
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url': url,
                                    },
                                    callback=self.parse_item,
                                    cb_kwargs={'url':url})
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = zpksItem()
            item['job'] = response.xpath('//h1/text()').extract_first()
            item['company_name'] = response.xpath('//*[@id="main"]/div[3]/div/div[2]/div[2]/div[4]/div[1]/text()').extract_first()
            item['industry'] = '互联网'
            item['location'] = response.xpath('//*[@id="main"]/div[1]/div/div/div[2]/p/text()').extract_first()
            item['salary'] = response.xpath('//*[@id="main"]/div[1]/div/div/div[2]/div[2]/span/text()').extract_first()
            item['time'] = ''
            item['website'] = 'boss直聘'
            item['link'] = kwargs['url']
            item['type'] = '1'
            item['source'] = 'boss直聘'
            item['content'] = ''.join(response.xpath('//*[@id="main"]/div[3]/div/div[2]/div[2]/div[2]/div').extract())
            item['education'] = ''
            item['spider_name'] = 'boss'
            item['module_name'] = 'boss直聘'
            print(
                "===========================>crawled one item" +
                response.request.url)
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)