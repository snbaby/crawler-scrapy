# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem


class AnhuiZfcgwSpider(scrapy.Spider):
    name = 'anhui_zfcgw'
    custom_settings = {
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'zhcx',  # 综合查询
                    'url': 'http://www.ccgp-anhui.gov.cn/cmsNewsController/getCgggNewsList.do?pageNum=1&numPerPage=20&title=&buyer_name=&agent_name=&proj_code=&bid_type=&type=&dist_code=&pubDateStart=&pubDateEnd=&pProviceCode=&areacode_city=&areacode_dist=&channelCode=sxqcg_cggg&three='
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'],
                                    args={
                                        'wait': 1
                },
                    callback=self.parse_page,
                    cb_kwargs=content, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response, kwargs))
        try:
            for pagenum in range(page_count):
                url = kwargs['url'].replace(
                    'pageNum=1', 'pageNum=' + str(pagenum + 1))
                yield SplashRequest(url,
                                    args={
                                        'wait': 1
                                    },
                                    callback=self.parse,
                                    cb_kwargs=kwargs, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.last::attr(onclick)').extract_first().split('\'')[1])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for tr in response.css('tbody tr'):
            try:
                title = tr.css(
                    'td:nth-child(1) a::attr(title)').extract_first()
                url = response.urljoin(
                    tr.css('td:nth-child(1) a::attr(href)').extract_first())
                region = tr.css(
                    'td:nth-child(1) a::text').extract_first().split('】')[0].replace('【', '').strip()
                time = tr.css(
                    'td:nth-child(2) a::text').extract_first().replace('[', '').replace(']', '').strip()
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time
                }
                yield scrapy.Request(url, callback=self.parse_item, cb_kwargs=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            title = kwargs['title']
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
            item['content'] = response.css('.frameNews').extract_first()
            item['appendix'] = ''
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '安徽省政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = kwargs['region']
            item['appendix_name'] = ''
            item['spider_name'] = 'anhui_zfcgw'
            item['txt'] = ''.join(response.css('.frameNews *::text').extract())
            item['module_name'] = '安徽-政府采购网'

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
