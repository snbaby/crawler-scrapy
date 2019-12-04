# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem

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
  splash:go("http://www.baidu.com")
  splash:wait(1)
  wait_for_element(splash, "#currpage")
  splash:wait(1)
  return {
    html = splash:html(),
  }
end
"""

class ZhejiangSpider(scrapy.Spider):
    name = 'zhejiang'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'szfbgtwj',  # 省政府办公厅文件
                    'url': 'http://www.zj.gov.cn/col/col1545735/index.html'
                },
                # {
                #     'topic': 'zcjd',  # 政策解读
                #     'url': 'http://www.zj.gov.cn/col/col1545738/index.html'
                # },
                # {
                #     'topic': 'jhzj',  # 计划总结
                #     'url': 'http://www.zj.gov.cn/col/col1544855/index.html'
                # }
            ]
            for content in contents:
                if content['topic'] == 'szfbgtwj':
                    yield SplashRequest(content['url'], args={'lua_source': script, 'endpoint': 'execute', 'wait': 1}, callback=self.parse_page, cb_kwargs=content, dont_filter=True)
                else:
                    yield SplashRequest(content['url'], callback=self.parse_page, cb_kwargs=content, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        print(response.text)
        return
        page_count = int(self.parse_pagenum(response, kwargs))
        page_count = 1
        try:
            for pagenum in range(page_count):
                if kwargs['topic'] == 'szfbgtwj':
                    ss = """
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
                      assert(splash:go("www.baidu.com"))
                      wait_for_element(splash, "#currpage")
                      assert(splash:wait(1))
                      splash:runjs("document.getElementById('a').value11 = 911")
                      wait_for_element(splash, "#currpage")
                      assert(splash:wait(1))
                      return {
                        html = splash:html()
                      }
                    end
                    """
                    yield SplashRequest(kwargs['url'], args={'lua_source': ss, 'wait': 1, 'endpoint': 'run'}, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
                else:
                    url = kwargs['url'] + '?uid=' + response.css(
                        '.zjszfxxlb div::attr(id)').extract_first() + '&pageNum=' + str(pagenum + 1)
                    yield SplashRequest(url, args={'lua_source': ss, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                if kwargs['topic'] == 'szfbgtwj':
                    return int(response.css(
                        'table.tb_title > tbody > tr > td:nth-child(2) a:nth-last-child(1)::text').extract_first())
                else:
                    return int(
                        response.css('.xc_pgLast::attr(href)').extract_first().split('pageNum=')[1])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        print(response.text)
        if kwargs['topic'] == 'szfbgtwj':
            for href in response.css('a[onmouseout]::attr(href)').extract():
                print(kwargs['topic'])
                print(href)
        else:
            for href in response.css('.xc_pgContainer a::attr(href)').extract():
                print(kwargs['topic'])
                print(href)
        return
        str = ''
        for text in response.css('body::text').extract():
            str = str + text.strip()
        res = json.loads(str)
        for doc in res['docs']:
            try:
                if 'pubtime' in doc:
                    url = doc['url']
                    title = doc['title']
                    time = doc['pubtime']
                    source = doc['src']
                    article_num = doc['fileno']
                    result = {
                        'url': url,
                        'title': title,
                        'time': time,
                        'source': source,
                        'article_num': article_num
                    }
                    yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)
