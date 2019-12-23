# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy_splash import SplashRequest
from utils.tools.attachment import get_attachments,get_times
import json

script ="""
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))
  return {
    html = splash:html(),
  }
end
"""

# splash lua script
script_click = """
         function main(splash, args)
             assert(splash:go(args.url))
             assert(splash:wait(args.wait))
             js = "[[document.querySelector('.pgStyle form input').value=2;document.querySelector('.pgStyle form button').click();]]"
             splash:runjs(js)
             assert(splash:wait(args.wait))
             return splash:html()
         end
         """


class QuanguoZuixinSpider(scrapy.Spider):
    name = 'fujian_zwgkzxd'
    custom_settings = {
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
            'scrapy_splash.SplashCookiesMiddleware': 140,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
    }
    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://www.fujian.gov.cn/zc/zwgkzxd/dzc/szfjszfbgtzcwj/"
            #yield SplashRequest(url, callback=self.parse_page, endpoint='execute', args={'lua_source': script, 'wait': 1})
            json_body={
                'js_source': "document.querySelector('#btnSearch').click();",
                'url' : url,
                'console': 1,
                'iframes': 1,
                'png': 1,
                'html': 1,
                'wait':3
            }
            yield scrapy.Request("http://47.106.239.73:8050/render.json",
                           method='POST',
                           headers={'Content-Type':'application/json'},
                           body=json.dumps(json_body),
                           callback=self.parse_result)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            #page_count = int(self.parse_pagenum(response))
            for i in range(1, 4):
                yield SplashRequest("http://www.fujian.gov.cn/zc/zwgkzxd/dzc/szfjszfbgtzcwj/", callback=self.parse_result, endpoint='execute',
                                args={
                                    'lua_source': script_click,
                                    'wait': 1
                                }, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_result(self, response):
        ret = json.loads(response.text)
        img = ret["png"]
        import  base64
        img  = base64.b64decode(img)
        with open('/tmp/picture_out.png', 'wb') as f:
            f.write(img)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                self.add_pagenum = response.css('.default_pgTotalPage::text').extract_first()
                logging.info("self.add_pagenum={}".format(self.add_pagenum))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
