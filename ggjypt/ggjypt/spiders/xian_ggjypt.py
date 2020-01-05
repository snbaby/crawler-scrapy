# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
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


class XianGgjyptSpider(scrapy.Spider):
    name = 'xian_ggjypt'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'gcjs',  # 工程建设项目招标投标
                    'url': 'http://www.sxggzyjy.cn/jydt/001001/001001001/subPage_jyxx.html'
                },
                {
                    'topic': 'tdsy',  # 土地使用权和矿业权出让
                    'url': 'http://www.sxggzyjy.cn/jydt/001001/001001002/subPage_jyxx.html'
                },
                {
                    'topic': 'gycq',  # 国有产权交易
                    'url': 'http://www.sxggzyjy.cn/jydt/001001/001001003/subPage_jyxx.html'
                },
                {
                    'topic': 'zfcg',  # 政府采购
                    'url': 'http://www.sxggzyjy.cn/jydt/001001/001001004/subPage_jyxx.html'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = kwargs['url']
                else:
                    url = kwargs['url'].replace(
                        'subPage.html', str(pagenum + 1) + '.html')
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs,
                                    dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(
                    response.css('#index::text').extract_first().split('/')[1].strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for href in response.css('.ewb-list a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.pares_item, cb_kwargs={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def pares_item(self, response, **kwargs):
        try:
            appendix, appendix_name = get_attachments(response)
            title = response.css('.article-title::text').extract_first()
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
            item['content'] = response.css('#mainContent').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.css(
                '.info-source::text').extract_first().strip().split('】')[1].split('：')[1].strip()
            item['source'] = response.css(
                '.info-source::text').extract_first().strip().split('】')[0].split('：')[1].strip()
            item['website'] = '陕西省公共资源交易信息网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '陕西省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'xian_ggjypt'
            item['txt'] = ''.join(
                response.css('#mainContent *::text').extract())
            item['module_name'] = '陕西省-公共交易平台'
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
