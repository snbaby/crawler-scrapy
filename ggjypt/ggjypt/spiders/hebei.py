# -*- coding: utf-8 -*-
import scrapy
import logging

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
  wait_for_element(splash, ".ewb-com-item")
  js = string.format("document.querySelector('%s > div > div > input[type=text]').value =%d", args.id,args.page)
  splash:evaljs(js)
  js1 = string.format("document.querySelector('%s > div > div > button').click()", args.id)
  splash:evaljs(js1)
  splash:runjs("document.querySelector('#iframe1 > ul').innerHTML=''")
  wait_for_element(splash, ".ewb-com-item")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'hebei_ggjypt'
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002001/subNoticeGov.html',
                    'id': '#page_001002001001'
                },
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002002/subNoticeGov.html',
                    'id': '#page_001002002001'
                },
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002004/subNoticeGov.html',
                    'id': '#page_001002004001'
                },
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002005/001002005001/subNoticeGovGJzb.html',
                    'id': '#page_001002005001001'
                },
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002005/001002005002/subNoticeGovGJzb.html',
                    'id': '#page_001002005002001'
                },
                {
                    'url': 'http://www.hebpr.gov.cn/hbjyzx/jydt/001002/001002006/subNoticeGov.html',
                    'id': '#page_001002006001'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                    endpoint = 'execute',
                    args={
                        'lua_source': script,
                        'id': content['id'],
                        'page': 1,
                        'url': content['url'],
                    },
                    callback=self.parse_page,
                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        print(page_count)
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    yield SplashRequest(response.meta['url'],
                        endpoint='execute',
                        args={
                            'lua_source': script,
                            'id': response.meta['id'],
                            'page': pagenum,
                            'url': response.meta['url'],
                        },
                        callback=self.parse,
                        meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//*[@class="m-pagination-page"]/li[last()]/a/text()').extract()[0]) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//li[@class="ewb-com-item"]'):
            try:
                item = {}
                item['title'] = selector.xpath('./div/a/text()').extract_first()
                item['time'] = selector.xpath('./span/text()').extract_first().strip()
                url = response.urljoin(selector.xpath('./div/a/@href').extract_first())
                print(url)
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        if response.meta['title']:
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
                item['content'] = "".join(response.xpath('//div[@class="content_scroll"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '河北省'
                item['time'] = response.meta['time']
                item['website'] = '河北省公共资源交易服务平台'
                item['module_name'] = '河北省-公共交易平台'
                item['spider_name'] = 'hebei_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="content_scroll"]//text()').extract())
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