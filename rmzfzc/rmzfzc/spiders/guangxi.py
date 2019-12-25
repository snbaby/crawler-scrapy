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

class GuangxiSpider(scrapy.Spider):
    name = 'guangxi'
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
                    'topic': 'xxgk',  # 信息公开
                    'url': 'http://fun.gxzf.gov.cn/php/index.php?c=file'
                },
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.gxzf.gov.cn/zcjd/index.shtml'
                },
                {
                    'topic': 'dfxfg',  # 地方性法规
                    'url': 'http://www.gxzf.gov.cn/zwgk/flfg/dfxfg/index.shtml'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response, kwargs))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = kwargs['url']
                else:
                    if kwargs['topic'] == 'xxgk':
                        url = kwargs['url'] + '&pageno='+str(pagenum+1)
                    else:
                        url = kwargs['url'].replace('.shtml', '-' + str(pagenum + 1) + '.shtml')
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                if kwargs['topic'] == 'xxgk':
                    return int(response.css('.more-page a:nth-child(1)::text').extract_first().split('条')[1].replace('页','').strip())
                else:
                    return int(response.css('.more-page a:nth-last-child(1)::attr(href)').extract_first().split('index-')[1].replace('.shtml', ''))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('.more-list a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                if url.endswith('.pdf'):
                    return
                if kwargs['topic'] == 'xxgk':
                    yield scrapy.Request(url, callback=self.parse_xxgk, cb_kwargs={'url': url}, dont_filter=True)
                elif kwargs['topic'] == 'zcjd':
                    yield scrapy.Request(url, callback=self.parse_zcjd_dfxfg, cb_kwargs={'url': url}, dont_filter=True)
                else:
                    yield scrapy.Request(url, callback=self.parse_zcjd_dfxfg, cb_kwargs={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_xxgk(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.people-desc tr:nth-child(2) td::text').extract_first().strip()
            item['article_num'] = response.css('.people-desc tr:nth-child(3) td::text').extract_first().strip()
            item['content'] = response.css('.article-con').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.people-desc tr:nth-child(3) td:nth-child(2)::text').extract_first().strip()
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '广西壮族自治区人民政府门户网站'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(response.css('.article-con *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '广西壮族自治区人民政府门户网站'
            item['spider_name'] = 'guangxi'
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

    def parse_zcjd_dfxfg(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.article h1::text').extract_first().strip()
            item['article_num'] = ''
            item['content'] = response.css('.article-con').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css('.article-inf-left::text').extract_first().split('来源：')[1].strip()
            item['time'] = response.css('.article-inf-left::text').extract_first().split('来源：')[0].strip()
            item['province'] = ''
            item['city'] = ''
            item['area'] = ''
            item['website'] = '广西壮族自治区人民政府门户网站'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(response.css('.article-con *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '广西壮族自治区人民政府门户网站'
            item['spider_name'] = 'guangxi'
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