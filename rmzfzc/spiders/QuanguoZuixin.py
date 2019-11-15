# -*- coding: utf-8 -*-
import scrapy

from scrapy_splash import SplashRequest

from rmzfzc.items import rmzfzcItem

script ="""
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""
class QuanguoZuixinSpider(scrapy.Spider):
    name = 'QuanguoZuixin'
    custom_settings = {
        'SPIDER_MIDDLEWARES':{
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 100,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 64,
        },

        'DUPEFILTER_CLASS':'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE':'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL' :'http://localhost:8050/'
    }

    def start_requests(self):
        url = 'http://sousuo.gov.cn/column/30469/1.htm'
        yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse)
        # retry middleware 指定重试几次

    def parse(self, response):
        for href in response.xpath('//ul[@class="listTxt"]/li/h4/a/@href'):
            print(href.extract())
            yield scrapy.Request(href.extract(), callback=self.parse_item, dont_filter=True)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        item = rmzfzcItem()
        item['title'] = response.css('.bd1 td::text').extract()[4]
        item['article_num'] = response.css('.bd1 td::text').extract()[5]
        item['content'] = response.text
        item['appendix'] = ''
        item['source'] = '中华人民共和国中央人民政府'
        item['time'] = response.css('.bd1 td::text').extract()[3]
        item['province'] = ''
        item['city'] = ''
        item['area'] = ''
        item['website'] = '中华人民共和国中央人民政府'
        item['link'] = response.request.url

        print("===========================>crawled one item")
        yield item