# -*- coding: utf-8 -*-
import scrapy

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

url = 'http://www.shandong.gov.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=6000&perpage=6000'

class AnhuiSpider(scrapy.Spider):
    name = 'shandong'
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
                    'topic':'zcjd',
                    'data':{'col': '1','webid': '4','path': 'http://www.shandong.gov.cn/','columnid': '2262','sourceContentType': '1','unitid': '5836','webname': '山东省人民政府','permissiontype': '0'}
                },
                {
                    'topic': 'zcwj',
                    'data': {'col': '1','webid': '4','path': 'http://www.shandong.gov.cn/','columnid': '2266','sourceContentType': '1','unitid': '5836','webname': '山东省人民政府','permissiontype': '0'}
                },
                {
                    'topic': 'zcwj',
                    'data': {'col': '1','webid': '4','path': 'http://www.shandong.gov.cn/','columnid': '2267','sourceContentType': '1','unitid': '5836','webname': '山东省人民政府','permissiontype': '0'}
                },
                {
                    'topic': 'zcwj',
                    'data': {'col': '1','webid': '4','path': 'http://www.shandong.gov.cn/','columnid': '2268','sourceContentType': '1','unitid': '5836','webname': '山东省人民政府','permissiontype': '0'}
                }
            ]
            for content in contents:
                yield scrapy.FormRequest(url, formdata=content['data'],
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'},
                                         callback=self.parse_page,cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        text = response.text.replace('<![CDATA[', '').replace(']]>','').replace(
            '<datastore>', '').replace('<nextgroup>', '').replace('<recordset>', '').replace('</recordset>','').replace('</datastore>','').replace(
            '<record>', '').replace('</nextgroup>', '')
        sel = scrapy.Selector(text=text)
        for href in sel.xpath('//*[@class="tit"]/a/@href').extract():
            time.sleep(0.5)
            try:
                yield scrapy.Request(href, callback=self.parse_item,
                                     dont_filter=True, cb_kwargs=kwargs)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            if kwargs['topic'] == 'zcjd':
                item['title'] = response.xpath(
                    '//*[@class="xq-tit"]/text()').extract_first()
                item['article_num'] = ''
                source = response.xpath('//*[@class="pl42"]/text()').extract_first()
                item['source'] = source.replace('来源：', '') if source else ''
                timeStr = response.xpath('//*[@class="R-tit"]/text()').extract_first() if response.xpath(
                    '//*[@class="R-tit"]/text()') else response.xpath('//*[@class="R-tit"]/span/text()').extract_first()
                item['time'] = timeStr.replace('时间：', '')
                item['content'] = "".join(response.xpath('//div[@class="article"]').extract())
                item['appendix'] = appendix
                item['province'] = '山东省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山东省人民政府'
                item['link'] = response.request.url
                item['txt'] = "".join(response.xpath('//div[@class="article"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '山东省人民政府'
                item['spider_name'] = 'shandong_zcjd'
            else:
                if response.xpath('//div[@class="people-desc"]'):
                    article_num = response.xpath(
                        '//*[@class="people-desc"]/table/tbody/tr[3]/td[1]/text()').extract_first()
                    item['title'] = response.xpath(
                        '//*[@class="people-desc"]/table/tbody/tr[2]/td[1]/text()').extract_first()
                    item['article_num'] = article_num.strip() if article_num else ''
                    item['source'] = response.xpath(
                        '//*[@class="people-desc"]/table/tbody/tr[1]/td[1]/text()').extract_first()
                    item['time'] = response.xpath(
                        '//*[@class="people-desc"]/table/tbody/tr[3]/td[2]/text()').extract_first()
                else:
                    item['title'] = response.xpath(
                        '//*[@class="xq-tit"]/text()').extract_first()
                    item['article_num'] = ''
                    source = response.xpath('//*[@class="pl42"]/text()').extract_first()
                    item['source'] = source.replace('来源：','') if source else ''
                    timeStr = response.xpath('//*[@class="R-tit"]/text()').extract_first() if response.xpath('//*[@class="R-tit"]/text()') else response.xpath('//*[@class="R-tit"]/span/text()').extract_first()
                    item['time'] = timeStr.replace('时间：','')
                item['appendix'] = appendix
                item['content'] = "".join(response.xpath('//div[@class="article"]').extract())
                item['province'] = '山东省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山东省人民政府'
                item['link'] = response.request.url
                item['txt'] = "".join(response.xpath('//div[@class="article"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['module_name'] = '山东省人民政府'
                item['spider_name'] = 'shandong_zfwj'
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