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

class HainanSpider(scrapy.Spider):
    name = 'hainan'
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
                    'topic': 'zcfg',  # 政策法规
                    'url': 'http://www.hainan.gov.cn/hainan/zcfg/zymylist.shtml'
                },
                {
                    'topic': 'zxjd',  # 最新解读
                    'url': 'http://www.hainan.gov.cn/hainan/zxjd/list3.shtml'
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
                if pagenum == 0:
                    url = response.meta['url']
                else:
                    url = response.meta['url'].replace(
                        '.shtml', '_' + str(pagenum+1) + '.shtml')
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('.pagination_index_last::text').extract()[2].split('条 共')[1].replace('页','').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.css('.list-right_title a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                response.meta['url'] = url
                yield scrapy.Request(url, callback=self.parse_item, dont_filter=True,meta=response.meta)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
            if len(response.css('ucaptitle::text').extract()) == 1:
                item = rmzfzcItem()
                item['title'] = response.css('ucaptitle::text').extract_first().strip()
                item['article_num'] = ''
                item['content'] = response.css('ucapcontent').extract_first()
                item['appendix'] = appendix
                item['source'] = response.css('#ly::text').extract_first()
                item['time'] = response.css('publishtime::text').extract_first().strip()
                item['province'] = '海南省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '海南省人民政府'
                item['link'] = response.meta['url']
                item['txt'] = ''.join(response.css('ucapcontent *::text').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '海南省人民政府'
                item['spider_name'] = 'hainan_'+response.meta['topic']
            else:
                item = rmzfzcItem()
                source = response.xpath('//*[@class="pages-date"]/span/text()').extract_first()
                item['title'] = response.css('table tr:nth-child(3) td:nth-child(2)::text').extract_first() if response.css('table tr:nth-child(3) td:nth-child(2)::text') else response.xpath('//*[@class="article oneColumn pub_border"]/h1/text()').extract_first()
                item['article_num'] = response.css('table tr:nth-child(4) td:nth-child(2)::text').extract_first()
                item['content'] = response.css('#UCAP-CONTENT').extract_first()
                item['appendix'] = appendix
                item['source'] = source.replace('来源：','') if source else ''
                item['time'] = response.css('table tr:nth-child(4) td:nth-child(4)::text').extract_first() if response.css('table tr:nth-child(4) td:nth-child(4)::text') else response.xpath('//*[@class="pages-date"]/text()').extract_first()
                item['province'] = '海南省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '海南省人民政府'
                item['link'] = response.meta['url']
                item['txt'] = ''.join(response.css('#UCAP-CONTENT *::text').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '海南省人民政府'
                item['spider_name'] = 'hainan_'+response.meta['topic']
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