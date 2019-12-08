# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
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
  assert(splash:wait(0.1))
  wait_for_element(splash, ".HeadStyleOfDataGridItemStyle")
  assert(splash:wait(0.1))
  splash:runjs("document.querySelector('.DataGrid').innerHTML = ''")
  assert(splash:wait(0.1))
  splash:runjs("__doPostBack('MoreInfoList1$Pager','2')")
  assert(splash:wait(0.1))
  wait_for_element(splash, ".HeadStyleOfDataGridItemStyle")
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
        test = """
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
          splash:runjs("document.querySelector('iframe').contentWindow.document.body.querySelector('#MoreInfoList1_Pager tr td:nth-child(2) a:nth-last-child(2)').click()")
          splash:wait(1)
          splash:runjs("document.querySelector('body').innerHTML = document.querySelector('iframe').contentWindow.document.body.querySelector('form').innerHTML")
          splash:wait(1)
          return splash:html()
        end
        """
        try:
            url = "http://gxggzy.gxzf.gov.cn/gxzbw/showinfo/jyxx.aspx?QuYu=450001&categoryNum=001010001"
            #yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
            yield SplashRequest(url,
                                endpoint='execute',
                                args={
                                    'lua_source': test,
                                    'wait': 1,
                                    'url': url,
                                },
                                callback=self.test)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def test(self,response):
        for title in response.css('#MoreInfoList1_tdcontent a::attr(title)').extract():
            print(title)

    def parse_type(self, response):
        for href in response.xpath('//*[@class="LeftMenuSub"]/a/@onclick'):
            for id in response.xpath('//*[@class="hubs"]/ul/li/@id'):
                try:
                    type = href.extract().replace('Openinfo(\'','').replace('\')','')
                    url = 'http://gxggzy.gxzf.gov.cn/gxzbw/showinfo/jyxx.aspx?QuYu=' + id.extract() + '&categoryNum=' + type
                    print(url)
                    content = {
                        'url': url
                    }
                    yield SplashRequest(url,
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'wait': 1,
                            'page': 1,
                            'url': url,
                        },
                        callback=self.parse_page,
                        cb_kwargs=content)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)

    def parse_page(self, response, **kwargs):
        logging.error(response.text)
        print(response.xpath('//*[@class="DataGrid"]/tr[2]/td[2]/a/text()').extract())
        return
        page_count = int(response.xpath('//*[@class="totalPageNum"]').re(r'([1-9]\d*\.?\d*)')[0]) + 1
        try:
            for pagenum in range(page_count):
                if pagenum > 1:
                    time.sleep(0.5)
                    print('pagenum' + str(pagenum))
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
        for selector in response.xpath('//*[@id="content"]/tr'):
            try:
                item = {}
                item['title'] = selector.xpath('./td[2]/a/text()').extract_first()
                item['time'] = selector.xpath('./td[3]/text()').extract_first()
                url = response.urljoin(selector.xpath('./td[2]/a/@href').extract_first())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
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
                item['content'] = "".join(response.xpath('//div[@class="message clearFloat jyxx"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '山西省'
                item['time'] = kwargs['time']
                item['website'] = '山西省公共资源交易服务平台'
                item['module_name'] = '山西省-公共交易平台'
                item['spider_name'] = 'shanxi_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="message clearFloat jyxx"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@class="message clearFloat jyxx"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@class="message clearFloat jyxx"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/@href').extract())
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