# -*- coding: utf-8 -*-
import scrapy
import logging
import time

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
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
          setTimeout(check, 200);
        } else if(Date.now() >= end) {
          var err = 'Timeout waiting for element';
          splash.error(err + " " + selector);
        } else {
          splash.resume('Element found');
        }
      }
      check();
    }
  ]], css, maxwait))
end

function main(splash, args)
  splash:go(args.url)
  wait_for_element(splash, ".layui-layer-content.layui-layer-loading1")
  assert(splash:wait(3))
  return splash:html()
end
"""

class TianJinSzfwjSpider(scrapy.Spider):
    name = 'sichuan_ggjypt'
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
        try:
            url = "http://ggzyjy.sc.gov.cn/jyxx/transactionInfo.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = "http://ggzyjy.sc.gov.cn/jyxx/transactionInfo.html"
                    yield SplashRequest(url,endpoint = 'execute', args={'lua_source': script, 'wait': 1,'url': url}, callback=self.parse,
                                        dont_filter=True)
                elif pagenum < 7 and pagenum > 1:
                    url = "http://ggzyjy.sc.gov.cn/jyxx/"+str(pagenum)+".html"
                    yield SplashRequest(url, endpoint='execute', args={'lua_source': script, 'wait': 1, 'url': url},
                                        callback=self.parse,
                                        dont_filter=True)
                elif pagenum > 6:
                    url = "http://ggzyjy.sc.gov.cn/jyxx/transactionInfo.html?categoryNum=002&pageIndex=" + str(pagenum)
                    yield SplashRequest(url, endpoint='execute', args={'lua_source': script, 'wait': 1, 'url': url},
                                        callback=self.parse,
                                        dont_filter=True)
                print(url + str(pagenum))
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            details = response.xpath('//*[@id="pager"]/script').re(r'([1-9]\d*\.?\d*)')[4]
            pageCount = response.xpath('//*[@id="pager"]/script').re(r'([1-9]\d*\.?\d*)')[3]
            if not self.add_pagenum:
                return int(details) / int(pageCount) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//ul[@class="comm-list"]/li/p'):
            try:
                item = {}
                item['title'] = selector.xpath('./a/text()').extract_first()
                item['time'] = selector.xpath('./span/text()').extract_first()
                url = response.urljoin(selector.xpath('./a/@href').extract_first())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response, **kwargs):
        if response.text:
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
                item['content'] = "".join(response.xpath('//div[@class="content"]').extract())
                item['source'] = '四川省公共资源交易服务平台'
                item['category'] = category
                item['type'] = ''
                item['region'] = '四川省'
                item['time'] = kwargs['time'].strip()
                item['website'] = '四川省公共资源交易服务平台'
                item['module_name'] = '四川省-公共交易平台'
                item['spider_name'] = 'sichuan_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="content"]//text()').extract())
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
