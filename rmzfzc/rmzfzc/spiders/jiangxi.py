# -*- coding: utf-8 -*-
import scrapy

import logging
from utils.tools.attachment import get_attachments,get_times
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class JiangxiSpider(scrapy.Spider):
    name = 'jiangxi'
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'szfwj',  # 省政府文件
                    'url': 'http://www.jiangxi.gov.cn/col/col443/index.html'
                },
                {
                    'topic': 'bmjd',  # 部门解读
                    'url': 'http://www.jiangxi.gov.cn/col/col5868/index.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        uid = response.css('.list div[id]::attr(id)').extract_first()
        try:
            for pagenum in range(page_count):
                url = response.meta['url'] + '?uid=' + uid + \
                    '&pageNum=' + str(pagenum + 1)
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.default_pgTotalPage::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.css(
                'ul:nth-child(1) .default_pgContainer a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                if response.meta['topic'] == 'szfwj':
                    yield scrapy.Request(url, callback=self.parse_szfwj, meta={'url': url, 'topic': response.meta['topic']}, dont_filter=True)
                else:
                    yield scrapy.Request(url, callback=self.parse_bmjd, meta={'url': url, 'topic': response.meta['topic']}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_szfwj(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = ''.join(response.css('.sp_title *::text').extract()).strip()
            item['article_num'] = response.css('.xxgkTitle tr:nth-child(1) td:nth-child(3)::text').extract_first().strip()
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.xxgkTitle tr:nth-child(2) td:nth-child(3)::text').extract_first().strip()
            item['province'] = '江西省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江西省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '江西省人民政府'
            item['spider_name'] = 'jiangxi'
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

    def parse_bmjd(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = ''.join(response.css('.sp_title *::text').extract()).strip()
            item['article_num'] = ''
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.sp_time font:nth-child(1)::text').extract_first().replace('发布时间：','')
            item['province'] = '江西省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江西省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '江西省人民政府'
            item['spider_name'] = 'jiangxi'
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
