# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
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
  assert(splash:wait(0.5))
  wait_for_element(splash, ".pg_num_input")
  js = string.format("document.querySelector('#target').value =%d", args.page)
  splash:evaljs(js)
  splash:runjs("document.querySelector('#toview').innerHTML=''")
  splash:runjs("document.querySelector('#moreinfo').click()")
  wait_for_element(splash, ".list-tbnew")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'chongqing_ggjypt'
    custom_settings = {
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
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'quanguo',  # 重庆市公共资源拍卖交易网
                    'url': 'https://www.cqggzy.com/jyxx/jyxx-page.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint = 'execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': 1,
                                        'url': content['url'],
                                    },
                                    callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(response.xpath('//*[@id="index"]').re(r'([1-9]\d*\.?\d*)')[1]) + 1
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    time.sleep(0.5)
                    yield SplashRequest(kwargs['url'],
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
                                            'page': pagenum,
                                            'url': kwargs['url'],
                                        },
                                        callback=self.parse,
                                        cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for selector in response.xpath('//*[@class="list-tbnew"]/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[4]/text()').extract_first()
                url = response.urljoin(selector.xpath('./td[2]/a/@href').extract_first())
                print(url)
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        if kwargs['title']:
            try:
                appendix, appendix_name = get_attachments(response)
                category = '其他';
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
                item = ztbkItem()
                item['title'] = title
                item['content'] = "".join(response.xpath('//div[@class="epoint-article-content"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '重庆市'
                item['time'] = get_times(kwargs['time'])
                item['website'] = '重庆市公共资源交易服务平台'
                item['module_name'] = '重庆市-公共交易平台'
                item['spider_name'] = 'chongqing_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="epoint-article-content"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.request.url
                item['appendix'] = appendix
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