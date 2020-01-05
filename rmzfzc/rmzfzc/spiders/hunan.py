# -*- coding: utf-8 -*-
import scrapy

import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(3))
  return splash:html()
end
"""


class HunanSpider(scrapy.Spider):
    name = 'hunan'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'fggz',  # 法规规章
                    'url': 'http://www.hunan.gov.cn/hnszf/xxgk/wjk/fggz/flfg.html'
                },
                {
                    'topic': 'bmjd',  # 部门解读
                    'url': 'http://www.hunan.gov.cn/hnszf/xxgk/jd/bmjd/index.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], endpoint='execute', args={'lua_source': script, 'wait': 1, 'url': content['url']},
                                    callback=self.parse_page,
                                    dont_filter=True,cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = kwargs['url']
                else:
                    url = kwargs['url'].replace(
                        '.html', '_' + str(pagenum + 1) + '.html')
                yield SplashRequest(url, endpoint='execute', args={'lua_source': script, 'wait': 1, 'url': url},
                                    callback=self.parse,
                                    dont_filter=True,
                                    cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            print(response)
            if not self.add_pagenum:
                return int(
                    response.css('.page_count span::text').extract_first().replace(
                        '共', '').replace(
                        '页', ''))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        if kwargs['topic'] == 'fggz':
            for href in response.css('.table a::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield SplashRequest(url,endpoint = 'execute', args={'lua_source': script, 'wait': 1,'url': url},
                                        callback=self.parse_fggz,
                                        cb_kwargs={'url': url})
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        else:
            for href in response.css(
                    '.yl-listbox > ul > li > a::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield scrapy.Request(url, callback=self.parse_bmjd, cb_kwargs={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)

    def parse_fggz(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.sp_title::text').extract_first().strip()
            item['article_num'] = response.css('.a1 > font:nth-child(2)::text').extract_first().replace('文号：', '').strip()
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = ''
            item['time'] = response.css('.a1 > font:nth-child(14)::text').extract_first().replace('发文日期：','').strip()
            item['province'] = '湖南省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '湖南省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '湖南省人民政府'
            item['spider_name'] = 'hunan_fggz'
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

    def parse_bmjd(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('.sp_title::text').extract_first().strip()
            item['article_num'] = ''
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css('.sp_time > span:nth-child(1)::text').extract_first()
            item['time'] = response.css('.time::text').extract_first().strip()
            item['province'] = '湖南省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '湖南省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = ''.join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '湖南省人民政府'
            item['spider_name'] = 'hunan_bmjd'
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
