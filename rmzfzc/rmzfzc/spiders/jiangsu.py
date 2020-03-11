# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(2))
  return {
    html = splash:html(),
  }
end
"""


class JiangsuSpider(scrapy.Spider):
    name = 'jiangsu'
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
                    'topic': 'szfjbgtwj',  # 省政府及办公厅文件
                    'url': 'http://www.jiangsu.gov.cn/col/col32646/index.html'
                },
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.jiangsu.gov.cn/col/col32648/index.html'
                },
                {
                    'topic': 'sjfg',  # 省级法规
                    'url': 'http://www.jiangsu.gov.cn/col/col59202/index.html'
                },
                {
                    'topic': 'gfxwj',  # 规范性文件
                    'url': 'http://www.jiangsu.gov.cn/col/col66109/index.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page, meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        uid = response.css('.bt-rig-cen-01 div::attr(id)').extract_first()
        try:
            for pagenum in range(page_count):
                url = response.meta['url'] + "?uid=" + \
                    uid + "&pageNum=" + str(pagenum + 1)
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
        for href in response.css('.main_list a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                if response.meta['topic'] == 'szfjbgtwj':
                    yield scrapy.Request(url, callback=self.parse_szfjbgtwj, meta={'url': url}, dont_filter=True)
                elif response.meta['topic'] == 'zcjd':
                    yield scrapy.Request(url, callback=self.parse_zcjd, meta={'url': url}, dont_filter=True)
                elif response.meta['topic'] == 'sjfg':
                    yield scrapy.Request(url, callback=self.parse_sjfg, meta={'url': url}, dont_filter=True)
                else:
                    yield scrapy.Request(url, callback=self.parse_gfxwj, meta={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_szfjbgtwj(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css(
                '.xxgk_table tr:nth-child(3) td:nth-child(2)::text').extract_first()
            item['article_num'] = response.css(
                '.xxgk_table tr:nth-child(4) td:nth-child(2)::text').extract_first()
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css(
                '.xxgk_table tr:nth-child(2) td:nth-child(4)::text').extract_first()
            item['province'] = '江苏省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江苏省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '江苏省人民政府'
            item['spider_name'] = 'jiangsu'
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

    def parse_zcjd(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.sp_title::text').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css(
                '.sp_time font:nth-child(2)::text').extract_first().replace('来源：', '')
            item['time'] = response.css(
                '.sp_time font:nth-child(1)::text').extract_first().replace('发布日期：', '')
            item['province'] = '江苏省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江苏省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '江苏省人民政府'
            item['spider_name'] = 'jiangsu'
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

    def parse_sjfg(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.sp_title::text').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css(
                '.sp_time font:nth-child(2)::text').extract_first().replace('来源：', '')
            item['time'] = response.css(
                '.sp_time font:nth-child(1)::text').extract_first().replace('发布日期：', '')
            item['province'] = '江苏省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江苏省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '江苏省人民政府'
            item['spider_name'] = 'jiangsu'
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

    def parse_gfxwj(self, response):
        try:
            item = rmzfzcItem()
            item['title'] = response.css(
                '.xxgk_table tr:nth-child(3) td:nth-child(2)::text').extract_first()
            item['article_num'] = response.css(
                '.xxgk_table tr:nth-child(4) td:nth-child(2)::text').extract_first()
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = ''
            item['source'] = ''
            item['time'] = response.css(
                '.xxgk_table tr:nth-child(2) td:nth-child(4)::text').extract_first()
            item['province'] = '江苏省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '江苏省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = ''
            item['module_name'] = '江苏省人民政府'
            item['spider_name'] = 'jiangsu'
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
