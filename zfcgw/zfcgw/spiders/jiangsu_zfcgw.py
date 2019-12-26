# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

class JiangsuZfcgwSpider(scrapy.Spider):
    name = 'jiangsu_zfcgw'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
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
        'SPLASH_URL': "http://39.100.240.19:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'zgysgg',  #资格预审公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/zgysgg/'
                },
                {
                    'topic': 'gkzbgg',  #公开招标公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/gkzbgg/'
                },
                {
                    'topic': 'yqzbgg',  #邀请招标公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/yqzbgg/'
                },
                {
                    'topic': 'jztbgg',  #竞争性谈判公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/jztbgg/'
                },
                {
                    'topic': 'jzqsgg',  #竞争性磋商公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/jzqsgg/'
                },
                {
                    'topic': 'dylygg',  #单一来源公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/dylygg/'
                },
                {
                    'topic': 'xjgg',  #询价公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/xjgg/'
                },
                {
                    'topic': 'zbgg',  #中标公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/zbgg/'
                },
                {
                    'topic': 'cgcjgg',  # 成交公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/cgcjgg/'
                },
                {
                    'topic': 'zzgg',  #废标（终止）公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/zzgg/'
                },
                {
                    'topic': 'cggzgg',  #更正公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/cggzgg/'
                },
                {
                    'topic': 'qtgg',  #其他公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/qtgg/'
                },
                {
                    'topic': 'htgg_1',  #合同公告
                    'url': 'http://www.ccgp-jiangsu.gov.cn/ggxx/htgg_1/'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum==0:
                    url = kwargs['url'] + 'index.html'
                else:
                    url = kwargs['url'] + 'index_' + str(pagenum)+'.html'
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs,dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                if len(''.join(response.css('.fanye::text').extract()).strip()) > 0:
                    return int(''.join(response.css('.fanye::text').extract()).split('，')[0].replace('共有','').replace('页','').strip())
                else:
                    return 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for li in response.css('#newsList li'):
            try:
                href = li.css('a::attr(href)').extract_first()
                time = li.css('::text').extract()[2].strip()
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.pares_item, cb_kwargs={'url': url, 'time': time},dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def pares_item(self, response, **kwargs):
        try:
            title = response.css('.dtit h1::text').extract_first().strip()
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
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            item['content'] = response.css('.detail_con').extract_first()
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '江苏政府采购'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '江苏'
            item['appendix_name'] = ''
            item['spider_name'] = 'jiangsu_zfcgw'
            item['txt'] = ''.join(response.css('.detail_con *::text').extract())
            item['module_name'] = '江苏-政府采购网'

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
