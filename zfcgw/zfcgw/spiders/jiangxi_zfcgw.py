# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""

class JiangxiZfcgwSpider(scrapy.Spider):
    name = 'jiangxi_zfcgw'
    custom_settings = {
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
                    'topic': 'cggg',  #采购公告
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006001/jyxx.html'
                },
                {
                    'topic': 'bggg',  #变更公告
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006002/jyxx.html'
                },
                {
                    'topic': 'dycq',  #答疑澄清
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006003/jyxx.html'
                },
                {
                    'topic': 'jggs',  #结果公示
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006004/jyxx.html'
                },
                {
                    'topic': 'dylygs',  #单一来源公示
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006005/jyxx.html'
                },
                {
                    'topic': 'htgs',  #合同公示
                    'url': 'http://www.ccgp-jiangxi.gov.cn/web/jyxx/002006/002006006/jyxx.html'
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
                url = kwargs['url'].replace('jyxx.html',str(pagenum+1) + '.html')
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
                return int(response.css('#index::text').extract_first().split('/')[1])
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for li in response.css('.ewb-list-node'):
            try:
                if kwargs['topic'] == 'htgs':
                    href = li.css('a::attr(href)').extract_first().strip()
                    title = li.css('a::text').extract_first().strip()
                    region = ''
                    time = li.css('.ewb-list-date::text').extract_first().strip()
                    url = response.urljoin(href)
                    result = {
                        'url':url,
                        'title':title,
                        'region':region,
                        'time':time
                    }
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1},callback=self.pares_htgs, cb_kwargs=result,dont_filter=True)
                else:
                    href = li.css('a::attr(href)').extract_first().strip()
                    title = ''.join(li.css('a *::text').extract()).strip()
                    region = title.split(']')[0].replace('[','').strip()
                    time = li.css('.ewb-list-date::text').extract_first().strip()
                    url = response.urljoin(href)
                    result = {
                        'url': url,
                        'title': title,
                        'region': region,
                        'time': time
                    }
                    yield scrapy.Request(url, callback=self.pares_item, cb_kwargs=result,dont_filter=True)

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def pares_item(self, response, **kwargs):
        try:
            appendix, appendix_name=get_attachments(response)
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
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            item['content'] = response.css('.article-info').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '江西公共资源交易网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = kwargs['region']
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'jiangxi_zfcgw'
            item['txt'] = ''.join(response.css('.article-info *::text').extract())
            item['module_name'] = '江西-政府采购网'

            print("===========================>crawled one item:url = {}, appendix={}, appendix_name={}"
                  .format(response.request.url, appendix, appendix_name))
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item

    def pares_htgs(self, response, **kwargs):
        try:
            appendix, appendix_name=get_attachments(response)
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
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            item['content'] = response.css('.fui-accordions').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '江西公共资源交易网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = kwargs['region']
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'jiangxi_zfcgw'
            item['txt'] = ''.join(response.css('.fui-accordions *::text').extract())
            item['module_name'] = '江西-政府采购网'

            print("===========================>crawled one item:url = {}, appendix={}, appendix_name={}"
                  .format(response.request.url, appendix, appendix_name))
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)
        yield item