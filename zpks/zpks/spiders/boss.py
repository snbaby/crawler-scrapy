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
  splash:wait(3)
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                'c101020100',
                'c101280100',
                'c101010100',
                'c101280600',
                'c101210100',
                'c101030100',
                'c101110100',
                'c101190400',
                'c101200100',
                'c101230200',
                'c101250100',
                'c101270100',
                'c101180100',
                'c101040100'
            ]
            for content in contents:
                page_count = 10
                for pagenum in range(page_count):
                    url = 'https://www.zhipin.com/'+content+'/?page='+str(pagenum+1)+'&ka=page-'+str(pagenum+1)
                    logging.info(url)
                    yield SplashRequest(url,
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'pagenum': pagenum + 1,
                            'url': url,
                        },
                        callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        logging.info(response.xpath('//div[@class="primary-wrapper"]/a/@href').extract())
        for href in response.xpath('//div[@class="primary-wrapper"]/a/@href').extract():
            try:
                url = response.urljoin(href)
                logging.info(url)
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url': url,
                                    },
                                    callback=self.parse_item,
                                    meta={'url':url})
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            item = zpksItem()
            item['job'] = response.xpath('//h1/text()').extract_first()
            item['company_name'] = response.xpath('//*[@id="main"]/div[3]/div/div[2]/div[2]/div[4]/div[1]/text()').extract_first()
            item['industry'] = '互联网'
            item['location'] = response.xpath('//*[@id="main"]/div[1]/div/div/div[2]/p/text()').extract_first()
            item['salary'] = response.xpath('//*[@id="main"]/div[1]/div/div/div[2]/div[2]/span/text()').extract_first()
            item['time'] = ''
            item['website'] = 'boss直聘'
            item['link'] = response.meta['url']
            item['type'] = '1'
            item['source'] = 'boss直聘'
            item['content'] = ''.join(response.xpath('//*[@id="main"]/div[3]/div/div[2]/div[2]/div[2]/div').extract())
            tmp = response.xpath('//*[@id="main"]/div[1]/div/div/div[2]/p//text()').extract()
            item['education'] = tmp[len(tmp)-1] if len(tmp)>0 else ''
            item['spider_name'] = 'boss'
            item['module_name'] = 'boss直聘'
            logging.info(
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