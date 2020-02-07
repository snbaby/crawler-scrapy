# -*- coding: utf-8 -*-
import scrapy

import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

class ShaanxiSpider(scrapy.Spider):
    name = 'shaanxi'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'szfwj',  # 省政府文件
                    'url': 'http://www.shaanxi.gov.cn/info/iList.jsp?node_id=GKszfbgt&file_head=%E9%99%95%E8%A5%BF%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C%E4%BB%A4&tm_id=69'
                },
                {
                    'topic': 'gfxwj',  # 规范性文件
                    'url': 'http://www.shaanxi.gov.cn/info/iList.jsp?node_id=GKszfbgt&tm_id=517'
                },
                {
                    'topic': 'szfcwhy',  # 省政府常务会议
                    'url': 'http://www.shaanxi.gov.cn/info/iList.jsp?cat_id=17585'
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
        try:
            for pagenum in range(page_count):
                url = response.meta['url'] + '&cur_page=' + str(pagenum + 1)
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('form span:nth-child(1)::text').extract_first().split('共')[1].replace('页','').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        if response.meta['topic'] == 'szfwj':
            for href in response.css('.gk_list_table a[title]::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield scrapy.Request(url, callback=self.parse_szfwj, meta={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        elif response.meta['topic'] == 'gfxwj':
            for href in response.css('.gk_list_table a[title]::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield scrapy.Request(url, callback=self.parse_gfxwj, meta={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        else:
            for href in response.css('.jd-tp-ul a::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield scrapy.Request(url, callback=self.parse_szfcwhy, meta={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)

    def parse_szfwj(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.zfwj_news_table tr:nth-child(3) .gk_news_table_title::text').extract_first().strip()
            item['article_num'] = response.css('.zfwj_news_table tr:nth-child(1) td:nth-child(4)::text').extract_first().strip()
            item['content'] = response.css('#info_content').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.zfwj_news_table tr:nth-child(4) td:nth-child(4)::text').extract_first().strip()
            item['province'] = '陕西省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '陕西省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#info_content *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '陕西省人民政府'
            item['spider_name'] = 'shaanxi'
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
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.gk_news_table tr:nth-child(3) .gk_news_table_title::text').extract_first().strip()
            item['article_num'] = response.css('.gk_news_table tr:nth-child(1) td:nth-child(4)::text').extract_first().strip()
            item['content'] = response.css('#info_content').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.gk_news_table tr:nth-child(2) td:nth-child(4)::text').extract_first().strip()
            item['province'] = '陕西省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '陕西省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#info_content *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '陕西省人民政府'
            item['spider_name'] = 'shaanxi'
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

    def parse_szfcwhy(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.info-tit h1::text').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('#info-cont').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css('#info_source::text').extract_first().strip()
            item['time'] = response.css('#info_released_dtime::text').extract_first().strip()
            item['province'] = '陕西省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '陕西省人民政府'
            item['link'] = response.meta['url']
            item['txt'] = ''.join(response.css('#info-cont *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '陕西省人民政府'
            item['spider_name'] = 'shaanxi'
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