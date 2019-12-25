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

class HainanGgjyptSpider(scrapy.Spider):
    name = 'hainan_ggjypt'
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
                    'topic': 'jsgc-zbgg',  # 建设工程-招标公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/jgzbgg/index.jhtml'
                },
                {
                    'topic': 'jsgc-zbgs',  # 建设工程-中标公示
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/jgzbgs/index.jhtml'
                },
                {
                    'topic': 'jsgc-qtgg',  # 建设工程-其他公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/jsqtgg/index.jhtml'
                },
                {
                    'topic': 'zfcg-cggg',  # 政府采购-采购公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/cggg/index.jhtml'
                },
                {
                    'topic': 'zfcg-zbgg',  # 政府采购-中标公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/cgzbgg/index.jhtml'
                },
                {
                    'topic': 'zfcg-qtgg',  # 政府采购-其他公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/zfcgqtgg/index.jhtml'
                },
                {
                    'topic': 'cqjy-gpgg',  # 产权交易-挂牌公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/gpgg/index.jhtml'
                },
                {
                    'topic': 'cqjy-cjgg',  # 产权交易-成交公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/cjgg/index.jhtml'
                },
                {
                    'topic': 'cqjy-yjcp',  # 产权交易-已经撤牌
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/cpgg/index.jhtml'
                },
                {
                    'topic': 'tdkc-crgg',  # 土地矿产-出让公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/crgg/index.jhtml'
                },
                {
                    'topic': 'tdkc-jggg',  # 土地矿产-结果公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/jggg/index.jhtml'
                },
                {
                    'topic': 'tdkc-qtgg',  # 土地矿产-其它公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/qtgg/index.jhtml'
                },
                {
                    'topic': 'ldhy-crgg',  # 林地海域-出让公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/hycrgg/index.jhtml'
                },
                {
                    'topic': 'ldhy-zbgg',  # 林地海域-招标公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/hyzbgg/index.jhtml'
                },
                {
                    'topic': 'ldhy-jggg',  # 林地海域-结果公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/hyjggg/index.jhtml'
                },
                {
                    'topic': 'yyqx-yygg',  # 医药医械-医药公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/yygg/index.jhtml'
                },
                {
                    'topic': 'yyqx-yxgg',  # 医药医械-医械公告
                    'url': 'http://zw.hainan.gov.cn/ggzy/ggzy/yxgg/index.jhtml'
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
                        '.jhtml', '_'+str(pagenum + 1) + '.jhtml')
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
                return int(response.css('.pagesite div::text').extract_first().split('/')[1].replace('页','').strip())
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        for tr in response.css('.newtable tr'):
            try:
                if len(tr.css('a[title]::attr(href)')) > 0:
                    url = response.urljoin(tr.css('a[title]::attr(href)').extract_first())
                    time = tr.css('td:nth-last-child(1)::text').extract_first()
                    yield scrapy.Request(url, callback=self.pares_item, cb_kwargs={'url': url,'time':time}, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def pares_item(self, response, **kwargs):
        try:
            title = response.css('title::text').extract_first().replace(' - 全国公共资源交易平台（海南省）','').strip()
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
            appendix, appendix_name = get_attachments(response)
            item['title'] = title
            item['content'] = response.css('.newsCon').extract_first()
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = response.css('.msgbar::text').extract_first().split('：')[2].replace('浏览次数','').strip()
            item['website'] = '海南省公共资源交易信息网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '海南省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'hainan_ggjypt'
            item['txt'] = ''.join(response.css('.newsCon *::text').extract())
            item['module_name'] = '海南省-公共交易平台'
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
