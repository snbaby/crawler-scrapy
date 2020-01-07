# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
import time
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
  wait_for_element(splash, ".one")
  splash:runjs("document.querySelector('document.querySelector('.content_right.fr > div:nth-child(4)').innerHTML = ''")
  js = string.format("pagination(%d)", args.page)
  splash:evaljs(js)
  assert(splash:wait(0.5))
  wait_for_element(splash, ".content_right.fr > div:nth-child(4) > table > tbody")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'neimenggu_ggjypt'
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/jsgcZbgg',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/jsgcGzsx',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/jsgcKbjl',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/jsgcZbhxrgs',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/jsgcZbjggs',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/zfcg/cggg',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/zfcg/gzsx',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/zfcg/zbjggs',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/tdAndKq/toCrggPage',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/tdAndKq/toCjqrPage',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/cqjy/crgg',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/cqjy/cjqr',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/qtjy/jygg',
                },
                {
                    'url': 'http://ggzyjy.nmg.gov.cn/jyxx/qtjy/jyqr',
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'page': 1,
                                        'url': content['url'],
                                    },
                                    callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    yield SplashRequest(kwargs['url'],
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'page': pagenum,
                                            'url': kwargs['url'],
                                        },
                                        callback=self.parse,
                                        cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//*[@class="mmggxlh"]/a[last()-1]/text()').extract()[0]) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse(self, response, **kwargs):
        for selector in response.xpath('//*[@class="content_right fr"]/div[4]/table/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[3]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[4]/text()').extract_first()
                url = response.urljoin(selector.xpath('./td[3]/a/@href').extract_first())
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
                item['title'] = title.strip()
                item['content'] = "".join(response.xpath('//div[@class="detail_contect"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '内蒙古自治区'
                item['time'] = kwargs['time'].strip()
                item['website'] = '内蒙古自治区公共资源交易服务平台'
                item['module_name'] = '内蒙古自治区-公共交易平台'
                item['spider_name'] = 'neimenggu_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="detail_contect"]//text()').extract())
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