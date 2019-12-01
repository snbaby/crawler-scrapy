# -*- coding: utf-8 -*-
import scrapy
import logging
import json

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

class NingxiaGgjyptSpider(scrapy.Spider):
    name = 'ningxia_ggjypt'
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
                    'topic': 'jygk',  # 交易公开
                    'url': 'http://www.nxggzyjy.org/ningxiaweb/002/1.html'
                },
                {
                    'topic': 'qlcgk',  # 土地使用权和矿业权出让
                    'url': 'http://www.nxggzyjy.org/ningxia/services/BulletinWebServer/getAllProcessCount?response=application/json&&strXiaQuCode=&strProjectJYType=&title='
                }
            ]
            for content in contents:
                yield SplashRequest(content['url'], args={'lua_source': script, 'wait': 1}, callback=self.parse_page,
                                    cb_kwargs=content)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        page_count = int(self.parse_pagenum(response,kwargs))
        try:
            for pagenum in range(page_count):
                if kwargs['topic'] == 'jygk':
                    url = kwargs['url'].replace('1.html', str(pagenum + 1) + '.html')
                else:
                    url = 'http://www.nxggzyjy.org/ningxia/services/BulletinWebServer/getAllProcessList?response=application/json&pageIndex='+str(pagenum + 1)+'&pageSize=15&&strXiaQuCode=&strProjectJYType=&title='
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, cb_kwargs=kwargs,dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                if kwargs['topic'] == 'jygk':
                    return int(response.css('#index::text').extract_first().split('/')[1].strip())
                else:
                    count = int(response.css('pre::text').extract_first().split(':')[1].replace('}',''))
                    page = count//15
                    if page * 15 == count:
                        page = page
                    else:
                        page = page + 1
                    return page
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        if kwargs['topic'] == 'jygk':
            for href in response.css('.ewb-info-a a::attr(href)').extract():
                try:
                    url = response.urljoin(href)
                    yield scrapy.Request(url, callback=self.pares_item, cb_kwargs={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)
        else:
            result = json.loads(response.css('pre::text').extract_first())
            data = json.loads(result.get('return'))
            Table = data.get('Table')
            for table in Table:
                try:
                    url = 'http://www.nxggzyjy.org/ningxiaweb/002/002002/002002001/'+table.get('infodate').split(' ')[0].replace('-','')+'/'+table.get('gonggaoguid')+'.html?jylcType='+table.get('processstep')
                    yield scrapy.Request(url, callback=self.pares_item, cb_kwargs={'url': url}, dont_filter=True)
                except Exception as e:
                    logging.error(self.name + ": " + e.__str__())
                    logging.exception(e)

        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def pares_item(self, response, **kwargs):
        try:
            if len(response.css('.article-title::text').extract()) > 0:
                title = response.css('.article-title::text').extract_first().strip()
            elif len(response.css('#title::text').extract()) > 0:
                title = response.css('#title::text').extract_first().strip()
            else:
                title = ''

            if len(response.css('.info-source::text').extract()) > 0:
                time = response.css('.info-source::text').extract_first().split('】')[0].split('时间：')[1].strip()
            else:
                time = response.css('.ewb-main-bar::text').extract_first().split('】')[0].split('时间：')[1].strip()

            if len(response.css('#mainContent').extract()) > 0:
                content = response.css('#mainContent').extract_first()
                txt = ''.join(response.css('#mainContent *::text').extract())
            else:
                content = response.css('div[data-role="body"]').extract_first()
                txt = ''.join(response.css('div[data-role="body"] *::text').extract())

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
            item['content'] = content
            item['appendix'] = ''
            item['category'] = category
            item['time'] = time
            item['source'] = ''
            item['website'] = '宁夏回族自治区公共资源交易信息网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '宁夏回族自治区'
            item['appendix_name'] = ''
            item['spider_name'] = 'ningxia_ggjypt'
            item['txt'] = txt
            item['module_name'] = '宁夏回族自治区-公共交易平台'

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