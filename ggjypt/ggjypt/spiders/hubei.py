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


class hubeiSzfwjSpider(scrapy.Spider):
    name = 'hubei_ggjypt'
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
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_type,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response, **kwargs):
        if kwargs['topic'] == 'dzzb':
            for href in response.xpath('//*[@class="ewb-sub-tree"]/li/a/@href'):
                try:
                    url = response.urljoin(href.extract())
                    print(url)
                    yield SplashRequest(url, callback=self.parse_page, dont_filter=True, cb_kwargs={'url': url})

                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        elif kwargs['topic'] == 'jzcg':
            print(kwargs['url'])
            yield SplashRequest(kwargs['url'], callback=self.parse_page1, dont_filter=True, cb_kwargs={'url': kwargs['url']})
        elif kwargs['topic'] == 'pmjy':
            print(kwargs['url'])
            yield SplashRequest(kwargs['url'], callback=self.parse_page2, dont_filter=True,
                                cb_kwargs={'url': kwargs['url']})

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response, '0'))
        print('page_count' + str(page_count))
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    temUrl = kwargs['url'].replace('moreinfo_jyxx.html', '')
                    url = temUrl + \
                          str(pagenum) + ".html" if pagenum > 1 else kwargs['url']
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page1(self, response, **kwargs):
        print(response)
        page_count = int(self.parse_pagenum(response, '1'))
        print('page_count' + str(page_count))
        page_count = page_count + 1
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    temUrl = 'http://www.hbyxjzcg.cn/drug/0-'
                    url = temUrl + \
                          str(pagenum) + ".html" if pagenum > 1 else kwargs['url']
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse1,
                                        dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_page2(self, response, **kwargs):
        print(response)
        page_count = int(self.parse_pagenum(response, '2'))
        print('page_count' + str(page_count))
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    params = {
                        'pageNumber': pagenum,
                        'pageSize': 10
                    }
                    url = "http://www.hbggzypm.com.cn/jygsnoticeController/jygsnoticelist"
                    yield SplashRequest(url, formdata=params, callback=self.parse2)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, type):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                if type == '0':
                    if response.xpath('//*[@class="ewb-page-li ewb-page-noborder ewb-page-num"]/span'):
                        return int(response.xpath('//*[@class="ewb-page-li ewb-page-noborder ewb-page-num"]/span').re(
                            r'([1-9]\d*\.?\d*)')[1])
                    else:
                        return '0'
                elif type == '1':
                    if response.xpath('//*[@class="flickr"]/a[4]/text()'):
                        return int(response.xpath('//*[@class="flickr"]/a[4]/text()').extract_first())
                    else:
                        return '0'
                elif type == '2':
                    details = response.xpath('//script')[4].re(r'([1-9]\d*\.?\d*)')[2]
                    pageCount = response.xpath('//script')[4].re(r'([1-9]\d*\.?\d*)')[1]
                    return int(details) / int(pageCount) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//ul[@class="ewb-news-items"]/li'):
            try:
                item = {}
                item['title'] = "".join(selector.xpath('./a//text()').extract())
                item['time'] = selector.xpath('./span/text()').extract_first().strip()
                url = selector.xpath('./a/@href').extract_first()
                print('url=============='+url)
                yield scrapy.Request(response.urljoin(url),callback=self.parse_item, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse1(self, response):
        print(len(response.xpath('//div[@class="boxwrap"]//ul[@class="news_list"]/li')))
        for selector in response.xpath('//div[@class="boxwrap"]//ul[@class="news_list"]/li'):
            try:
                item = {}
                item['title'] = "".join(selector.xpath('./a//text()').extract())
                item['time'] = selector.xpath('./span/text()').extract_first().strip()
                url = selector.xpath('./a/@href').extract_first()
                print('url=============='+url)
                yield scrapy.Request(response.urljoin(url),callback=self.parse_item1, dont_filter=True, cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse2(self, response):
        for selector in response.xpath('//ul[@class="ewb-news-items"]/li'):
            try:
                item = {}
                item['title'] = "".join(selector.xpath('./a//text()').extract())
                item['time'] = selector.xpath('./span/text()').extract_first().strip()
                url = selector.xpath('./a/@href').extract_first()
                print('url=============='+url)
                yield scrapy.Request(response.urljoin(url),callback=self.parse_item, dont_filter=True, cb_kwargs=item)
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
                item['content'] = "".join(response.xpath('//div[@class="entry"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '湖北省'
                item['time'] = kwargs['time']
                item['website'] = '湖北省公共资源交易服务平台'
                item['module_name'] = '湖北省-公共交易平台'
                item['spider_name'] = 'hubei_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="entry"]//text()').extract())
                item['appendix_name'] = ";".join(response.xpath('//div[@class="entry"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/text()').extract())
                item['link'] = response.request.url
                item['appendix'] = ";".join(response.xpath('//div[@class="entry"]//a[contains(@href,"pdf") or contains(@href,"doc") or contains(@href,"docx") or contains(@href,"xls")]/@href').extract())
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

    def parse_item1(self, response, **kwargs):
        if response.text:
            try:
                appendix, appendix_name = get_attachments(response)
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
                item['content'] = "".join(response.xpath('//div[@class="entry"]').extract())
                item['source'] = response.xpath('//a[@class="originUrl"]/text()').extract_first()
                item['category'] = category
                item['type'] = ''
                item['region'] = '湖北省'
                item['time'] = kwargs['time']
                item['website'] = '湖北省公共资源交易服务平台'
                item['module_name'] = '湖北省-公共交易平台'
                item['spider_name'] = 'hubei_ggjypt'
                item['txt'] = "".join(response.xpath('//div[@class="entry"]//text()').extract())
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
