# -*- coding: utf-8 -*-
import scrapy
import logging
import time

from scrapy_splash import SplashRequest
from yyqx.items import yyqxItem
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
  splash.images_enabled = false
  splash:go(args.url)
  splash:wait(1)
  wait_for_element(splash, "#goInt")
  js = string.format("document.querySelector('#goInt').value =%d", args.page)
  splash:evaljs(js)
  splash:runjs("document.querySelector('#content > div > table:nth-child(2)').innerHTML=''")
  splash:runjs("document.querySelector('#content > div > table:nth-child(4) > tbody > tr > td:nth-child(8) > input[type=image]').click()")
  wait_for_element(splash, "#content > div > table:nth-child(2) > tbody > tr")
  return splash:html()
end
"""

class YyqxSpider(scrapy.Spider):
    name = 'yyqx'
    custom_settings = {
        'CONCURRENT_REQUESTS': 30,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'yyqx',  # 医药器械
                    'url': 'http://app1.sfda.gov.cn/datasearchcnda/face3/base.jsp?tableId=26&tableName=TABLE26&title=%B9%FA%B2%FA%C6%F7%D0%B5&bcId=152904417281669781044048234789'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                    endpoint = 'execute',
                    args={
                        'lua_source': script,
                        'wait': 3,
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
        print(page_count)
        try:
            for pagenum in range(page_count):
                print(pagenum)
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

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return int(response.xpath('//*[@id="content"]/table[4]/tbody/tr/td[1]').re(r'([1-9]\d*\.?\d*)')[2]) + 1
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for selector in response.xpath('//*[@id="content"]/table[2]/tbody/tr/td/p/a/@href'):
            try:
                href = selector.re(r'([1-9]\d*\.?\d*)')[2]
                url = 'http://mobile.cfda.gov.cn/datasearch/QueryRecord?tableId=26&searchF=ID&searchK='+href
                print('url===========' + url)
                yield scrapy.Request(url, callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            datas = eval(response.text)
            print(datas)
            if datas[0]:
                item = yyqxItem()
                item['registration_code'] = datas[0]['CONTENT']
                item['registrar'] = datas[1]['CONTENT']
                item['registrar_address'] = datas[2]['CONTENT']
                item['production_address'] = datas[3]['CONTENT']
                item['agent_name'] = ''
                item['agent_address'] = ''
                item['name'] = datas[4]['CONTENT']
                specifications = datas[6]['CONTENT']
                item['specifications'] = specifications.replace('\n', '').replace('\r', '')
                compose = datas[7]['CONTENT']
                item['compose'] = compose.replace('\n', '').replace('\r', '')
                item['scope'] = datas[8]['CONTENT']
                item['other'] = datas[11]['CONTENT']
                remark = datas[12]['CONTENT']
                item['remark'] = remark.replace('\n', '').replace('\r', '')
                item['approval_date'] = get_times(datas[14]['CONTENT'])
                item['period_of_validity'] = get_times(datas[15]['CONTENT'])
                item['appendix'] = datas[10]['CONTENT']
                item['product_standard'] = datas[9]['CONTENT']
                remark = datas[16]['CONTENT']
                item['change_date'] = remark.replace('\n', '').replace('\r', '').replace('\u3000', '') \
                    .replace('<br>', '')
                item['zip_code'] = ''
                item['major_component'] = ''
                item['usage'] = ''
                item['storage_conditions'] = datas[9]['CONTENT']
                item['approval_dept'] = ''
                item['category'] = ''
                modify = ''
                item['modify'] = modify.replace('\n', '').replace('\r', '')
                try:
                    notes = ''
                    item['notes'] = notes.replace('\n', '').replace('\r', '')

                except:
                    item['notes'] = ''
                item['website'] = '国家食品药品监督局'
                item['link'] = response.url
                item['spider_name'] = 'yyqx'
                item['module_name'] = '医药器械'
                print(
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

