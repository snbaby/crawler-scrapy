# -*- coding: utf-8 -*-
import scrapy
import logging

from cnki_kjbg.items import cnkiKjbgItem
from scrapy_splash import SplashRequest


url = 'http://r.cnki.net/KNS/request/SearchHandler.ashx'
data = {
    "curpage": "1",
    "RecordsPerPage": "5000",
    "turnpage": "1",
    "tpagemode": "U",
    "dbPrefix": "KJBG",
    "Fields": "",
    "DisplayMode": "custommode",
    "PageName": "ASP.brief_result_aspx",
    "tokenstr": "uYuiM7d8Lar9/GrSpqt4gR7rokDxJTJ0jTLIwEPGxJWaGQAQssY3C+e8io/rEAwlcbkXGLmmD4Kdrk1jumRhr1bpx5YqtjXmEVqL/mmo593pbCNqblIp7x18fLpo0CSnzqxMwRd3jFGrYS/MZjsw5oDPwKTvn7a27Eg/u6UhUbijwEdmo9Jh5MzCUvh3YDGuDPZg6ShAXiab8kBoNbLGgrZ4JwdU0QGPnZ8FXz2V3rGoApXBsjyotfj2p4bphfGkQcsF/mb4D9E1lEOsrfqpfDahp1X5wJXC1XKiHszF+T6KO60BSfxEjm+dvO8oFwLxFhVo9Uup4x/pJQANNKzKCos0Vla4qyBI6EgxrfSplyigiN9M55QwC9pfudgH7RruV4PJhwAvqzIxGaoEkkwfTeDn7owEIKNK",
    "sortcode": "43782",
    "sortorder": "desc"
}
header = {
    'Content-Type': 'application/x-www-form-urlencoded'
}
class KjbgSpider(scrapy.Spider):
    name = 'kjbg'
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
            for num in range(40):
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
                    item['ask_num'] = selector.xpath('.//div[@class="s-gre"]/span[1]/text()').extract_first()
                    item['type'] = selector.xpath('.//div[@class="s-gre"]/span[2]/text()').extract_first()
                    item['pub_year'] = selector.xpath('.//div[@class="s-gre"]/span[3]/text()').extract_first()
                    url = selector.xpath('.//h1[@class="s-title"]/a/@href').extract_first()
                    url = url.replace('/kns','http://r.cnki.net/KCMS')
                    yield scrapy.Request(url, callback=self.parse_item, dont_filter=True, meta=item)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self,response):
        try:
            item = cnkiKjbgItem()
            item['title'] = response.meta['title']
            item['article_link'] = response.xpath('//a[@class="link-url"]/@href').extract_first()
            item['ask_num'] = response.meta['ask_num'].replace('索取号：','').strip()
            item['pub_year'] = response.meta['pub_year'].replace('发表年度：','').strip()
            item['type'] = response.meta['type'].replace('报告类型：','').strip()
            for selor in response.xpath('//table[@class="mc_table1 mc_table1_kjbg"]/tr'):
                if selor.xpath('./td[1]/text()').extract_first() == '【作者】':
                    item['author'] = selor.xpath('./td[2]/text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【机构来源】':
                    item['org_name'] = selor.xpath('./td[2]/text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【关键词】':
                    print(''.join(selor.xpath('./td[2]//text()').extract()))
                    item['keyword'] = ''.join(selor.xpath('./td[2]//text()').extract())
                elif selor.xpath('./td[1]/text()').extract_first() == '【页数】':
                    item['page_num'] = selor.xpath('./td[2]/text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【出版地】':
                    item['pub_address'] = selor.xpath('./td[2]/text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【发行号】':
                    item['pub_num'] = selor.xpath('./td[2]/text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【摘要】':
                    item['intro'] = selor.xpath('./td[2]//text()').extract_first()
                elif selor.xpath('./td[1]/text()').extract_first() == '【合作机构】':
                    item['org_cooperation'] = selor.xpath('./td[2]//text()').extract_first()
            item['website'] = '中国知网'
            item['link'] = response.request.url
            item['spider_name'] = 'kjbg'
            item['module_name'] = '科技报告'
            print("===========================>crawled one item" +
                  response.request.url)
            yield item
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
