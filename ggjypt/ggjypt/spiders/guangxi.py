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
  assert(splash:wait(1))
  js = string.format("document.getElementsByTagName('iframe')[0].contentWindow.__doPostBack('MoreInfoList1$Pager','%d')", args.page)
  splash:evaljs(js)
  assert(splash:wait(1))
  splash:runjs("document.querySelector('body').innerHTML = document.getElementsByTagName('iframe')[0].contentWindow.document.body.querySelector('form').innerHTML")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'guangxi_ggjypt'
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://gxggzy.gxzf.gov.cn/gxzbw/showinfo/jyxx.aspx?QuYu=450001&categoryNum=001010001"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        num = 1
        for href in response.xpath('//*[@class="LeftMenuSub"]/a/@onclick'):
            for id in response.xpath('//*[@class="hubs"]/ul/li/@id'):
                try:
                    type = href.extract().replace('Openinfo(\'','').replace('\')','')
                    url = 'http://gxggzy.gxzf.gov.cn/gxzbw/showinfo/jyxx.aspx?QuYu=' + id.extract() + '&categoryNum=' + type
                    content = {
                        'url': url
                    }
                    yield SplashRequest(url,
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'page': 2,
                            'url': url,
                        },
                        callback=self.parse_page,
                        cb_kwargs=content)

                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(response.xpath('//*[@id="MoreInfoList1_Pager"]//b/text()').extract()[1])
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
        for selector in response.xpath('//*[@class="DataGrid"]/tbody/tr'):
            try:
                if selector.xpath('./td[2]/a/text()'):
                    item = {}
                    item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                    item['time'] = selector.xpath('./td[3]/text()').extract_first()
                    url = 'http://gxggzy.gxzf.gov.cn' + selector.xpath('./td[2]/a/@href').extract_first()
                    item['url'] = url
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
                item['content'] = "".join(response.xpath('//div[@class="infodetail"]').extract())
                item['source'] = ''
                item['category'] = category
                item['type'] = ''
                item['region'] = '广西壮族自治区'
                item['time'] = kwargs['time']
                item['website'] = '广西壮族自治区公共资源交易服务平台'
                item['module_name'] = '广西壮族自治区-公共交易平台'
                item['spider_name'] = 'shanxi_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="infodetail"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = kwargs['url']
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