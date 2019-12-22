# -*- coding: utf-8 -*-
import scrapy
from utils.tools.attachment import get_attachments,get_times
import logging

from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
import time
from utils.tools.attachment import get_attachments

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

data = {
    'PageId': 3,
    'Count': 10,
    'ThemeCategoryNames': '行政规范性文件,行政规章,其他公文,法规',
    'TitleLength': 100,
    'TimeRight': 'yyyy-MM-dd',
    'DepartmentId': 0
}
url = 'http://www.cq.gov.cn/Ajax/AjaxPage'

class AnhuiSpider(scrapy.Spider):
    name = 'chongqing'
    custom_settings = {
        'CONCURRENT_REQUESTS': 30,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
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
                    'data':{
                        'PageId': 1,
                        'Count': 10000,
                        'ThemeCategoryNames': '行政规范性文件,行政规章,其他公文,法规',
                        'TitleLength': 100,
                        'TimeRight': 'yyyy-MM-dd',
                        'DepartmentId': 0
                    }
                },
                {
                    'data': {
                        'PageId': 1,
                        'Count': 10000,
                        'ThemeCategoryNames': '行政规章',
                        'TitleLength': 100,
                        'TimeRight': 'yyyy-MM-dd',
                        'DepartmentId': 0
                    }
                },
                {
                    'data': {
                        'PageId': 1,
                        'Count': 10000,
                        'ThemeCategoryNames': '行政规范性文件',
                        'TitleLength': 100,
                        'TimeRight': 'yyyy-MM-dd',
                        'DepartmentId': 1
                    }
                },
                {
                    'data': {
                        'PageId': 1,
                        'Count': 10000,
                        'ThemeCategoryNames': '行政规范性文件',
                        'TitleLength': 100,
                        'TimeRight': 'yyyy-MM-dd',
                        'DepartmentId': 94
                    }
                },
                {
                    'data': {
                        'PageId': 1,
                        'Count': 10000,
                        'ThemeCategoryNames': '其他公文',
                        'TitleLength': 100,
                        'TimeRight': 'yyyy-MM-dd',
                        'DepartmentId': 0
                    }
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(url, formdata={'partialViewName': '市政府文件', 'parameters': str(content['data'])},
                     headers={'Content-Type': 'application/x-www-form-urlencoded',
                              'Referer': 'http://www.cq.gov.cn/zwgk/szfwj'}, callback=self.parse_page,cb_kwargs=content['data'])
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        for selector in response.xpath('//*[@class="list"]/li'):
            time.sleep(0.5)
            item = {}
            item['title'] = selector.xpath('./a/text()').extract_first()
            item['link'] = 'http://www.cq.gov.cn' + selector.xpath('./a/@href').extract_first()
            item['time'] =  selector.xpath('./i/text()').extract_first()
            try:
                print(item['link'])
                yield scrapy.Request(item['link'], callback=self.parse_item,
                                     dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = kwargs['title']
            item['article_num'] = response.css('.govDetailTable tr:nth-child(4) td:nth-child(2)::text').extract_first()
            item['content'] = "".join(response.xpath('//div[@class="govIntro"]').extract())
            item['appendix'] = appendix
            item['source'] = response.css('.govDetailTable tr:nth-child(2) td:nth-child(2)::text').extract_first()
            item['time'] = kwargs['time']
            item['province'] = '重庆市'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '重庆市人民政府'
            item['link'] = kwargs['link']
            item['txt'] = "".join(response.xpath('//div[@class="govIntro"]//text()').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '重庆市人民政府'
            item['spider_name'] = 'chongqing'
            item['time'] = get_times(item['time'])
            print(
                "===========================>crawled one item" +
                response.request.url)
            yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
