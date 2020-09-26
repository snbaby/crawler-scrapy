# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class GuizhouZfcgwSpider(scrapy.Spider):
    name = 'guizhou_zfcgw'
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
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter'
    }

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'cgxqgg',  # 综合查询
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153332561072666.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153332561072666'
                },
                {
                    'topic': 'cggg',  # 采购公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153418052184995.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153418052184995'
                },
                {
                    'topic': 'gzgg',  # 更正公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153454200156791.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153454200156791'
                },
                {
                    'topic': 'fbgg',  # 废标公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153488085289816.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153488085289816'
                },
                {
                    'topic': 'zbcjgg',  # 中标(成交)公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153531755759540.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153531755759540'
                },
                {
                    'topic': 'dylygs',  # 单一来源公示
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153567415242344.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153567415242344'
                },
                {
                    'topic': 'dylycjgg',  # 单一来源(成交)公告
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1153595823404526.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1153595823404526'
                },
                {
                    'topic': 'zgys',  # 资格预审
                    'url': 'http://www.ccgp-guizhou.gov.cn/list-1156071132711523.html?siteId=1',
                    'post_url': 'http://www.ccgp-guizhou.gov.cn/article-search.html',
                    'category.id': '1156071132711523'
                }
            ]
            for content in contents:
                yield scrapy.Request(content['url'],
                                     callback=self.parse_page,
                                     headers={
                                         'Accept': '*/*',
                                         'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
                                     },
                                     meta=content,
                                     dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                url = response.meta['post_url']
                data = {
                    'siteId': '1',
                    'category.id': response.meta['category.id'],
                    'areaName': '',
                    'tenderRocurementPm': '',
                    'beginDate': '',
                    'endDate': '',
                    'keywords': '',
                    'articlePageNo': str(pagenum + 1),
                    'articlePageSize': '15'
                }
                yield scrapy.FormRequest(url=url,
                                         headers={
                                             'Accept': '*/*',
                                             'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
                                         },
                                         formdata=data, method='POST', dont_filter=True, callback=self.parse,
                                         meta=response.meta)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.css('.page ul li:nth-last-child(3) a::text').extract_first())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for li in response.css('.xnrx ul li'):
            try:
                title = li.css('a::text').extract_first()
                url = response.urljoin(li.css('a::attr(href)').extract_first())
                time = li.css('span::text').extract_first()
                result = {
                    'url': url,
                    'title': title,
                    'time': time
                }
                yield scrapy.Request(url,
                                     headers={
                                         'Accept': '*/*',
                                         'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36'
                                     },
                                     callback=self.parse_item, meta=result, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
            title = response.meta['title']
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
            item['content'] = response.css('#info').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '贵州省政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '贵州省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'guizhou_zfcgw'
            item['txt'] = ''.join(response.css('#info *::text').extract())
            item['module_name'] = '贵州-政府采购网'
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
