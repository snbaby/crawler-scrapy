# -*- coding: utf-8 -*-
import scrapy
import logging

from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
from scrapy_splash import SplashRequest


url = 'http://r.cnki.net/KNS/request/SearchHandler.ashx'
data = {
    "curpage": "1",
    "RecordsPerPage": "5000",
    "turnpage": "1",
    "tpagemode": "U",
    "dbPrefix": "CGXX",
    "DisplayMode": "custommode",
    "PageName": "ASP.brief_result_aspx",
    "tokenstr": "RmoleHoqaiJV7W6wm9WfR8JH7GpdOlKsR426DHEq64ejonl264dA4K607TzgO/++KqRhB7n/tw1AkEBDFjsnnu9sXcSUQXbxFKkdc69IN8b+oZ3xCpF0a3pHny97f7QOjGjgceoO8xsaivN2wiLLMpwKc/0X+bj2QaDMuMRI6m0+XJyCIRJAiPAyEQnyqh3+4ObN8pW6/J8lPfmNJROnHPsOLFP0mPzWLqtHM5fVcLWMOiRfu1AIKOrNpBCAekl/",
    "sortcode": "43476",
    "sortorder": "desc"
}
header = {
    'Content-Type': 'application/x-www-form-urlencoded'
}
class ZwcgSpider(scrapy.Spider):
    name = 'zwcg'
    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            for num in range(1900):
                data['curpage'] = str(num)
                yield scrapy.FormRequest(url, formdata=data,
                     headers=header,
                     callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self,response):
        try:
            if len(response.xpath('//*[@class="s-detail fl"]')) > 0:
                for selector in response.xpath('//*[@class="s-detail fl"]'):
                    item = {}
                    item['title'] = selector.xpath('.//h1[@class="s-title"]/a/text()').extract_first()
                    item['time'] = selector.xpath('.//div[@class="s-gre"]/span[1]/text()').extract_first()
                    item['region'] = selector.xpath('.//div[@class="s-gre"]/span[4]/text()').extract_first()
                    url = selector.xpath('.//h1[@class="s-title"]/a/@href').extract_first()
                    url = url.replace('/kns','http://r.cnki.net/KCMS').strip()
                    yield scrapy.Request(url, callback=self.parse_item, dont_filter=True, meta=item)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response):
        print(response.xpath('//span[@id="chTitle"]/text()').extract_first())
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
            item['content'] = "".join(response.xpath('//div[@class="vF_detail_content"]').extract())
            item['appendix'] = appendix
            item['category'] = category
            item['source'] = '中国知网'
            item['website'] = '中国知网'
            item['link'] = response.request.url
            item['type'] = '2'
            item['region'] = response.meta['region'].replace('省份：','')
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'zgzwcg'
            item['txt'] = "".join(response.xpath('//div[@class="vF_detail_content"]//text()').extract())
            item['module_name'] = '知网采购'
            item['time'] = get_times(response.meta['time'])
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