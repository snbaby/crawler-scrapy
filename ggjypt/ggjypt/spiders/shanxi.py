# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

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
  wait_for_element(splash, ".layui-laypage-btn")
  js = string.format("document.querySelector('.layui-input').value =%d", args.page)
  splash:evaljs(js)
  splash:runjs("document.querySelector('.layui-laypage-btn').click()")
  wait_for_element(splash, ".layui-laypage-btn")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'shanxi_ggjypt'
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
                    'topic': 'pmjy',  # 山西省公共资源拍卖交易网
                    'url': 'http://www.hbggzypm.com.cn/informController/informQuery'
                },
                {
                    'topic': 'pmjy',  # 山西省公共资源拍卖交易网
                    'url': 'http://www.hbggzypm.com.cn/jynoticeController/tojynoticelist'
                },
                {
                    'topic': 'pmjy',  # 山西省公共资源拍卖交易网
                    'url': 'http://www.hbggzypm.com.cn/jygsnoticeController/tojygsnoticelist'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint = 'execute',
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
        page_count = int(int(response.xpath('//*[@class="layui-laypage-count"]').re(r'([1-9]\d*\.?\d*)')[0])/10 + 1) + 1
        print('page_count' + str(page_count))
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
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
        for selector in response.xpath('//*[@class="list_table"]/tbody/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[3]//text()').extract_first()
                if selector.xpath('./td[2]/a/@onclick'):
                    id = selector.xpath('./td[2]/a/@onclick').extract_first().replace('javascript:informDetail(\'','').replace('\');','')
                    url = 'http://www.hbggzypm.com.cn:80/informController/informDetail?id=' + id
                else:
                    url = response.urljoin(selector.xpath('./td[2]/a/@href').extract_first())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        print('kwargs====' + str(kwargs))
        if kwargs['title']:
            try:
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
                item['content'] = "".join(response.xpath('//div[@class="zwbf"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '山西省'
                item['time'] = kwargs['time']
                item['website'] = '山西省公共资源交易服务平台'
                item['module_name'] = '山西省-公共交易平台'
                item['spider_name'] = 'shanxi_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="zwbf"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@class="zwbf"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@class="zwbf"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/@href').extract())
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