# -*- coding: utf-8 -*-
import scrapy

import logging
from scrapy_splash import SplashRequest
from rmzfzc.items import rmzfzcItem
from utils.tools.attachment import get_attachments,get_times
script = """
function main(splash, args)
  splash:go("http://www.baidu.com")
  splash:wait(1)
  wait_for_element(splash, "#currpage")
  splash:wait(1)
  return {
    html = splash:html(),
  }
end
"""


class ZhejiangSpider(scrapy.Spider):
    name = 'zhejiang'
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
            contents = [
                {
                    'topic': 'zcjd',  # 政策解读
                    'url': 'http://www.zj.gov.cn/col/col1545738/index.html'
                },
                {
                    'topic': 'jhzj',  # 计划总结
                    'url': 'http://www.zj.gov.cn/col/col1544855/index.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], callback=self.parse_page, cb_kwargs=content, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response, kwargs))
        print(page_count)
        try:
            for pagenum in range(page_count):
                url = kwargs['url'] + '?uid=' + response.css(
                    '.zjszfxxlb div::attr(id)').extract_first() + '&pageNum=' + str(pagenum + 1)

                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('.xc_pgLast::attr(href)').extract_first().split('pageNum=')[1])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('.xc_pgContainer a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url,callback=self.parse_item,cb_kwargs={'url':url},dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            item = rmzfzcItem()
            appendix, appendix_name = get_attachments(response)
            item['title'] = response.css('meta[name="ArticleTitle"]::attr(content)').extract_first()
            item['article_num'] = ''
            item['content'] = response.css('#zoom').extract_first()
            item['appendix'] = appendix
            item['source'] = response.css('meta[name="contentSource"]::attr(content)').extract_first()
            item['time'] = response.css('meta[name="Maketime"]::attr(content)').extract_first()
            item['province'] = '浙江省'
            item['city'] = ''
            item['area'] = ''
            item['website'] = '浙江省人民政府'
            item['link'] = kwargs['url']
            item['txt'] = "".join(response.css('#zoom *::text').extract())
            item['appendix_name'] = appendix_name
            item['module_name'] = '浙江省人民政府'
            item['spider_name'] = 'zhejiang'
            item['time'] = get_times(item['time'])
            print("===========================>crawled one item" + response.request.url)
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
        yield item