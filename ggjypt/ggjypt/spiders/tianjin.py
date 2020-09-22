# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times

class TianJinSzfwjSpider(scrapy.Spider):
    name = 'tianjin_ggjypt'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 2,
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://47.57.108.128:8050/"}



    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://60.28.163.169/jyxx/index_1.jhtml"
            yield scrapy.Request(url, callback=self.parse_type, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        for href in response.xpath('//ul[@class="menu_list"]/li/h3/@onclick'):
            try:
                url = href.extract()
                url = url.replace('window.location=\'','').replace('\'','').replace('http://ggzy.zwfwb.tj.gov.cn:80','http://60.28.163.169')
                yield scrapy.Request(url, callback=self.parse_page,headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_page(self, response):
        page_count = self.parse_pagenum(response)
        try:
            for pagenum in range(page_count):
                url = response.url.replace('.jhtml', '')+'_' + str(pagenum+1) + ".jhtml"
                yield scrapy.Request(url, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                result = response.css('body > div.content-warp > div.jyxxcontent > div > div > ul > li:nth-last-child(2) > a::attr(onclick)').extract_first()
                if result == "location.href='index.jhtml';":
                    return 1
                else:
                    return int(result.replace("location.href='index_","").replace(".jhtml';",""))
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//div[@class="article-list3-t"]/a/@url'):
            try:
                url = response.urljoin(href.extract()).replace('http://ggzy.zwfwb.tj.gov.cn:80','http://60.28.163.169')
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        if response.text:
            try:
                appendix, appendix_name = get_attachments(response)
                category = '其他';
                title = response.xpath('//div[@class="content-title"]/text()').extract_first() if response.xpath('//div[@class="content-title"]/text()') else response.xpath('//div[@class="div-title"]/text()').extract_first()
                time = response.xpath('//div[@id="time"]/text()').extract_first() if response.xpath('//div[@id="time"]/text()') else response.xpath('//div[@class="div-title2"]/text()').extract_first()
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
                item = ztbkItem()
                item['title'] = title
                item['content'] = "".join(response.xpath('//div[@id="content"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '天津市'
                item['time'] = time
                item['website'] = '天津市公共资源交易服务平台'
                item['module_name'] = '天津市-公共交易平台'
                item['spider_name'] = 'tianjin_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@id="content"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.request.url
                item['appendix'] = appendix
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
