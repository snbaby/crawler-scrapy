# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from ggjypt.items import ztbkItem

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class hubeiSzfwjSpider(scrapy.Spider):
    name = 'hubei_ggjypt'
    custom_settings = {
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            contents = [
                {
                    'topic': 'dzzb',  # 湖北省电子招标投标交易平台
                    'url': 'http://www.hbggzy.cn/jydt/003001/003001001/moreinfo_jyxx.html'
                },
                {
                    'topic': 'jzcg',  # 湖北省药械集中采购服务平台
                    'url': 'http://www.hbyxjzcg.cn/drug/0-1.html'
                },
                {
                    'topic': 'pmjy',  # 湖北省公共资源拍卖交易网
                    'url': 'http://www.hbggzypm.com.cn/'
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response, **kwargs):
        if kwargs['topic'] == 'dzzb':
            for href in response.xpath('//ul[@class="menu_body"]/li/@onclick'):
                try:
                    url = href.extract()
                    url = url.replace('window.location=\'', '').replace('\'', '')
                    print(url)
                    yield SplashRequest(url, callback=self.parse_page, dont_filter=True, cb_kwargs={'url': url})

                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        elif kwargs['topic'] == 'dzzb':
            


    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                temUrl = kwargs['url'].replace('.jhtml', '')+'_'
                url = temUrl + \
                      str(pagenum) + ".jhtml" if pagenum > 0 else kwargs['url']
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            size = len(response.xpath('//div[@class="pages"]/ul/li[1]').re(r'([1-9]\d*\.?\d*)'))
            return int(response.xpath('//div[@class="pages"]/ul/li[1]').re(r'([1-9]\d*\.?\d*)')[size-1])
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//ul[@class="article-list2"]/li/div'):
            try:
                item = {}
                item['title'] = "".join(selector.xpath('./a//text()').extract())
                item['time'] = selector.xpath('./div/text()').extract_first()
                url = selector.xpath('./a/@href').extract_first()
                print('url=============='+url)
                yield scrapy.Request(url,callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response, **kwargs):
        if response.text:
            try:
                category = '其他';
                title = kwargs['title']
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
                item['content'] = "".join(response.xpath('//div[@class="div-article2"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '湖北省'
                item['time'] = kwargs['time']
                item['website'] = '湖北省公共资源交易服务平台'
                item['module_name'] = '湖北省-公共交易平台'
                item['spider_name'] = 'hubei_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="div-article2"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@class="div-article2"]//a[contains(@href,"pdf") and contains(@href,"doc") and contains(@href,"docx") and contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@class="div-article2"]//a[contains(@href,"pdf") and contains(@href,"doc") and contains(@href,"docx") and contains(@href,"xls")]/@href').extract())
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