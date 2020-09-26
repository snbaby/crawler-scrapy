# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments, get_times


class GuangdongZfcgwSpider(scrapy.Spider):
    name = 'guangdong_zfcgw'
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
            url = 'http://www.gdgpo.gov.cn/queryMoreInfoList.do'
            for pageNum in range(self.parse_pagenum()):
                data = {
                    'channelCode': '0005',
                    'pointPageIndexId': '1',
                    'pageIndex': str(pageNum + 1),
                    'pageSize': '15'
                }
                yield scrapy.FormRequest(url=url, formdata=data, method='POST', callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return 26
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for li in response.css('.m_m_c_list li'):
            try:
                title = li.css('a[title]::attr(title)').extract_first()
                url = response.urljoin(li.css('a[title]::attr(href)').extract_first())
                region = li.css('span a::text').extract_first()
                time = li.css('em::text').extract_first()
                result = {
                    'url': url,
                    'title': title,
                    'region': region,
                    'time': time
                }
                yield scrapy.Request(url, callback=self.parse_item, meta=result, dont_filter=True)
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
            item['content'] = response.css('.zw_c_c_cont').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.meta['time']
            item['source'] = ''
            item['website'] = '广东省政府采购网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '广东省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'guangdong_zfcgw'
            item['txt'] = ''.join(response.css('.zw_c_c_cont *::text').extract())
            item['module_name'] = '广东省-政府采购网'
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
