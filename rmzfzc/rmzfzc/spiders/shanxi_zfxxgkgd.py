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
    name = 'shanxi_zfxxgkgd'
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
        'SPLASH_URL': 'http://localhost:8050/'}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "http://www.shanxi.gov.cn/zw/zfgkzl/zfxxgkgd/index.shtml"
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
                    url = "http://www.shanxi.gov.cn/zw/zfgkzl/zfxxgkgd/index_" + \
                        str(pagenum) + ".shtml" if pagenum > 0 else "http://www.shanxi.gov.cn/zw/zfgkzl/zfxxgkgd/index.shtml"
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
                return int(response.xpath('//div[@class="shanxi-gov-page-box mt20"]/p/script').re(r'([1-9]\d*\.?\d*)')[26])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//td[@class="affaires-doc-title"]/a/@href'):
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
                item['article_num'] = response.xpath('//span[contains(text(),"〔")]/text()').extract_first()
                item['time'] = response.xpath('//*[@class="article-infos-source left"]/span[contains(@alt,"时间")]/text()').extract_first()
                item['content'] = "".join(response.xpath('//div[@class="TRS_Editor"]').extract())
                item['source'] = response.xpath('//*[@class="article-infos-source left"]/span[contains(@alt,"来源")]/@alt').extract_first().replace('来源：','')
                item['province'] = '山西省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山西省人民政府'
                item['module_name'] = '山西省人民政府-政务公开法规政策'
                item['spider_name'] = 'shanxi_zfxxgkgd'
                item['txt'] = "".join(response.xpath('//div[@class="TRS_Editor"]//text()').extract())
                item['appendix_name'] = appendix_name
                item['link'] = response.request.url
                item['appendix'] = appendix
                item['time'] = get_times(item['time'])
            else:
                item['title'] = response.xpath('//td[contains(@colspan,"3")]/text()').extract_first()
                item['article_num'] = response.xpath('//td[@class="affairs-detail-head-cnt"]/text()').extract()[4] if response.xpath('//td[@class="affairs-detail-head-cnt"]/text()') else response.css('.bd1 td::text').extract()[5]
                item['time'] = response.xpath('//td[@class="affairs-detail-head-cnt"]/text()').extract()[5] if response.xpath('//td[@class="affairs-detail-head-cnt"]/text()') else response.css('.bd1 td::text').extract()[6]
                item['content'] = "".join(response.xpath('//*[@id="UCAP-CONTENT"]').extract())
                item['source'] = response.xpath('//td[@class="affairs-detail-head-cnt"]/text()').extract()[2] if response.xpath('//td[@class="affairs-detail-head-cnt"]/text()') else response.css('.bd1 td::text').extract()[2]
                item['province'] = '山西省'
                item['city'] = ''
                item['area'] = ''
                item['website'] = '山西省人民政府'
                item['module_name'] = '山西省人民政府-政务公开法规政策'
                item['spider_name'] = 'shanxi_zfxxgkgd'
                item['txt'] = "".join(response.xpath('//*[@id="UCAP-CONTENT"]//text()').extract())
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
