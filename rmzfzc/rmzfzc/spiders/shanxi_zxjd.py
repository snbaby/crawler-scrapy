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


class BeijingZfwjSpider(scrapy.Spider):
    name = 'shanxi_zxjd'
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
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': 'http://47.106.239.73:8050/'}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://www.shanxi.gov.cn/yw/zcjd/latest_1447.shtml"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            print('page_count====' + str(page_count))
            # 在解析翻页数之前，首先解析首页内容
            for pagenum in range(page_count):
                if pagenum<page_count:
                    url = "http://www.shanxi.gov.cn/yw/zcjd/latest_1447_" + \
                        str(pagenum) + ".shtml" if pagenum > 0 else "http://www.shanxi.gov.cn/yw/zcjd/latest_1447.shtml"
                    print('url==='+url)
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//div[@class="shanxi-gov-page-box"]/p/script').re(r'([1-9]\d*\.?\d*)')[27])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//*[@class="tab-flag-construck"]/ul/li/a/@href'):
            try:
                print('url===' + href.extract())
                url = response.urljoin(href.extract())
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            if response.xpath('//*[@class="detail-article-title oflow-hd"]/h5/text()').extract_first():
                item['title'] = response.xpath('//*[@class="detail-article-title oflow-hd"]/h5/text()').extract_first()
                item['article_num'] = ''
                item['time'] = response.xpath('//*[@class="article-infos-source left"]/span[contains(@alt,"时间")]/text()').extract_first()
                item['content'] = "".join(response.xpath('//div[@class="TRS_Editor"]').extract()) if response.xpath('//div[@class="TRS_Editor"]') else "".join(response.xpath('//div[@class="article-body oflow-hd"]').extract())
                item['source'] = response.xpath('//*[@class="article-infos-source left"]/span[contains(@alt,"来源")]/@alt').extract_first().replace('来源：','')
                item['province'] = '山西省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山西省人民政府'
                item['module_name'] = '山西省人民政府-最新解读'
                item['spider_name'] = 'shanxi_zxjd'
                item['txt'] = "".join(response.xpath('//div[@class="TRS_Editor"]//text()').extract()) if response.xpath('//div[@class="TRS_Editor"]') else "".join(response.xpath('//div[@class="article-body oflow-hd"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.request.url
                item['appendix'] = appendix
                item['time'] = get_times(item['time'])
            else:
                item['title'] = response.xpath('//div[@class="detail-article-title oflow-hd"]/h2/text()').extract_first()
                item['article_num'] = response.xpath('//div[@class="detail-article-title oflow-hd"]/h3/text()').extract_first()
                item['time'] = response.xpath('//span[contains(@alt,"时间")]/text()').extract_first()
                item['content'] = "".join(response.xpath('//*[@class="TRS_Editor"]').extract())
                item['source'] = response.xpath('//span[contains(@alt,"来源")]/text()').extract_first()
                item['province'] = '山西省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山西省人民政府'
                item['module_name'] = '山西省人民政府-最新解读'
                item['spider_name'] = 'shanxi_zxjd'
                item['txt'] = "".join(response.xpath('//*[@class="TRS_Editor"]//text()').extract())
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
