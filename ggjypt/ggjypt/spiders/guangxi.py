# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
import time
from utils.tools.attachment import get_attachments, get_times

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
  splash:runjs("document.querySelector('#MoreInfoList1_tdcontent').innerHTML=''")
  js = string.format("__doPostBack('MoreInfoList1$Pager','%d')", args.page)
  splash:evaljs(js)
  wait_for_element(splash, ".DataGrid")
  assert(splash:wait(1))
  return splash:html()
end
"""

url = "http://gxggzy.gxzf.gov.cn/gxzbw/showinfo/MoreInfo.aspx?QuYu=450001&categoryNum=001004001"


class GansuSpider(scrapy.Spider):
    name = 'guangxi_ggjypt'
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
        'SPLASH_URL': "http://47.57.108.128:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1, 'page': 1, 'url': url, },
                                callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': pagenum + 1,
                                        'url': url,
                                    },
                                    callback=self.parse,
                                    dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css(
                    '#MoreInfoList1_Pager > table > tbody > tr > td:nth-child(1) > font:nth-child(2) > b::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.css('.DataGrid tr'):
            try:
                if selector.css('td:nth-child(2) a::text'):
                    item = {}
                    item['title'] = selector.css('td:nth-child(2) a::attr(title)').extract_first()
                    item['time'] = selector.css('td:nth-child(3)::text').extract_first().strip()
                    item['url'] = response.urljoin(selector.css('td:nth-child(2) a::attr(href)').extract_first())
                    yield scrapy.Request(item['url'], callback=self.parse_item, dont_filter=True, meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
            category = '其他';
            title = response.meta['title']
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
            item['content'] = response.css('.infodetail').extract_first()
            item['source'] = ''
            item['category'] = category
            item['type'] = ''
            item['region'] = '广西壮族自治区'
            item['time'] = response.meta['time']
            item['website'] = '广西壮族自治区公共资源交易服务平台'
            item['module_name'] = '广西壮族自治区-公共交易平台'
            item['spider_name'] = 'guangxi_ggjypt'
            item['txt'] = ''.join(response.css('.infodetail *::text').extract())
            item['appendix_name'] = appendix_name
            item['link'] = response.meta['url']
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
