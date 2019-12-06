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
  splash:go("http://www.zj.gov.cn/col/col1545735/index.html")
  assert(splash:wait(0.5))
  wait_for_element(splash, ".btn_page")
  js = string.format("document.querySelector('#currpage').value =%d", args.page)
  splash:evaljs(js)
  splash:runjs("document.querySelector('.btn_page').click()")
  wait_for_element(splash, ".btn_page")
  return splash:html()
end
"""

class GansuSpider(scrapy.Spider):
    name = 'gansu'
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
        # 'ITEM_PIPELINES': {
        #     'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
        #     'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        # },
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
                    'topic': 'jyxxlb',  # 交易信息列表
                    'url': 'http://ggzyjy.gansu.gov.cn/f/newprovince/annogoods/list'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    endpoint = 'execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'page': 40,
                                        'url':"https://www.baidu.com",
                                    },
                                    callback=self.parse,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response,**kwargs):
        print('---------')
        print(response.css('#div1545735 > table > tbody > tr > td > table:nth-child(3) > tbody > tr:nth-child(2) > td:nth-child(3) > a::text').extract_first())
        pass
