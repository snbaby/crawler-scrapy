# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times
from scrapy.selector import Selector

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class XizangGgjyptSpider(scrapy.Spider):
    name = 'xizang_ggjypt'
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
        'SPLASH_URL': "http://47.57.108.128:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'zbzsgg',  # 招标资审报告
                    'url': 'http://www.xzggzy.gov.cn:9090/zbzsgg/index.jhtml'
                },
                # {
                #     'topic': 'jyjggg',  # 交易结果公告
                #     'url': 'http://www.xzggzy.gov.cn:9090/jyjggg/index.jhtml'
                # },
                # {
                #     'topic': 'zbwjcq',  # 招标文件澄清
                #     'url': 'http://www.xzggzy.gov.cn:9090/zbwjcq/index.jhtml'
                # },
                # {
                #     'topic': 'zgysjg',  # 资格预审结果
                #     'url': 'http://www.xzggzy.gov.cn:9090/zgysjg/index.jhtml'
                # },
                # {
                #     'topic': 'td',  # 成交公示
                #     'url': 'http://www.xzggzy.gov.cn:9090/td/index.jhtml'
                # },
                # {
                #     'topic': 'cq',  # 挂牌结果
                #     'url': 'http://www.xzggzy.gov.cn:9090/cq/index.jhtml'
                # },
                # {
                #     'topic': 'jyjg',  # 交易结果
                #     'url': 'http://www.xzggzy.gov.cn:9090/jyjg/index.jhtml'
                # },
                # {
                #     'topic': 'zrbqyxx',  # 转让标企业信息
                #     'url': 'http://www.xzggzy.gov.cn:9090/zrbqyxx/index.jhtml'
                # },
                # {
                #     'topic': 'zrbgdxx',  # 转让标股东信息
                #     'url': 'http://www.xzggzy.gov.cn:9090/zrbgdxx/index.jhtml'
                # },
                # {
                #     'topic': '',  # 采购/资审公告
                #     'url': 'http://www.xzggzy.gov.cn:9090/zfcg/index.jhtml'
                # },
                # {
                #     'topic': 'zbgg',  # 中标公告
                #     'url': 'http://www.xzggzy.gov.cn:9090/zbgg/index.jhtml'
                # },
                # {
                #     'topic': 'gzsx',  # 更正事项
                #     'url': 'http://www.xzggzy.gov.cn:9090/gzsx/index.jhtml'
                # }
            ]
            for content in contents:
                yield scrapy.Request(content['url'], callback=self.parse_page,
                                    meta=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                if pagenum == 0:
                    url = response.meta['url']
                else:
                    url = response.meta['url'].replace(
                        '.jhtml', '_' + str(pagenum + 1) + '.jhtml')
                yield scrapy.Request(url, callback=self.parse, meta=response.meta, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(Selector(text=response.text.split('</html>')[1]).css(
                    '.pages-list li:nth-child(1) a::text').extract_first().split('/')[1].replace('页', '').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in Selector(text=response.text.split('</html>')[1]).css('.article-list-old a::attr(href)').extract():
            try:
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.pares_item, meta={'url': url}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def pares_item(self, response):
        try:
            appendix, appendix_name = get_attachments(response)
            title = response.css('.div-title::text').extract_first().strip()
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
            item['content'] = response.css('.div-article2').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = response.css(
                '.div-title2::text').extract_first().split('浏览')[0].replace('发布时间：', '').strip()
            item['source'] = ''
            item['website'] = '西藏自治区公共资源交易信息网'
            item['link'] = response.meta['url']
            item['type'] = '2'
            item['region'] = '西藏自治区'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'xizang_ggjypt'
            item['txt'] = ''.join(
                response.css('.div-article2 *::text').extract())
            item['module_name'] = '西藏-公共交易平台'
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
