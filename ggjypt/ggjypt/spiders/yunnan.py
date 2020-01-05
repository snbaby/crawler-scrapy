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
  wait_for_element(splash, "#data_tab")
  splash:runjs("document.querySelector('#data_tab').innerHTML = ''")
  js = string.format("pagination(%d)", args.page)
  splash:evaljs(js)
  assert(splash:wait(0.5))
  wait_for_element(splash, "#data_tab")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'yunnan_ggjypt'
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
                    'url': 'https://www.ynggzy.com/jyxx/jsgcZbgg?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/jsgcBgtz'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/jsgcpbjggs?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/jsgcZbjggs?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/jsgcZbyc?area=000'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/zfcg/cggg?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/zfcg/gzsx?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/zfcg/zbjggs?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/zfcg/zfcgYcgg?area=000&secondArea='
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/kyqcr/zpgCrgg?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/kyqcr/bytz?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/kyqcr/zpgCrjggs?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/cqjy/crgg?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/cqjy/bytz?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/cqjy/cjqr?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/qtjy/crgg?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/qtjy/bgtz?'
                },
                {
                    'url': 'https://www.ynggzy.com/jyxx/qtjy/cjqr?'
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
        print('page_count' + str(page_count))
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
        for selector in response.xpath('//*[@id="data_tab"]/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[3]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[last()]/text()').extract_first()
                url = response.urljoin(selector.xpath('./td[3]/a/@href').extract_first())
                print('url===='+url)
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        if kwargs['title']:
            try:
                appendix, appendix_name = get_attachments(response)
                category = '其他';
                title = kwargs['title'].strip()
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
                if response.xpath('//div[@class="detail_contect"]'):
                    content = "".join(response.xpath('//div[@class="detail_contect"]').extract())
                    txt = "".join(response.xpath('//div[@class="detail_contect"]//text()').extract())
                elif response.xpath('//div[@class="page_contect bai_bg"]'):
                    content = "".join(response.xpath('//div[@class="page_contect bai_bg"]').extract())
                    txt = "".join(response.xpath('//div[@class="page_contect bai_bg"]//text()').extract())
                item['content'] = content
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '云南省'
                item['time'] = kwargs['time']
                item['website'] = '云南省公共资源交易服务平台'
                item['module_name'] = '云南省-公共交易平台'
                item['spider_name'] = 'yunnan_ggjypt'
                item['txt'] = txt
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