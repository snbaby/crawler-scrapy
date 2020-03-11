# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from xtgs.items import xtgsItem
from utils.tools.attachment import get_times

script = """
function main(splash, args)
  assert(splash:go(args.url))
  assert(splash:wait(1))
  return {
    html = splash:html(),
  }
end
"""


class TianJinSzfwjSpider(scrapy.Spider):
    name = 'xtgs_xtc'
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
        'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            url = "https://www.xintuochi.com/xtgs/?_p1.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        page_count = int(self.parse_pagenum(response))
        print(page_count)
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    url = 'https://www.xintuochi.com/xtgs/?_p' + str(pagenum) + '.html'
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//*[@class="assxx_fy"]/ul/li[last()-1]/a/@href').re(r'([1-9]\d*?\d*)')[0]) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//form[@class="ff"]/table/tr[position()>1]'):
            try:
                item = {}
                url = response.urljoin(selector.xpath('./td[1]/a/@href').extract_first())
                print(url)
                item['avg_yield'] = selector.xpath('./td[2]/text()').extract_first()
                item['pro_hold_rate'] = selector.xpath('./td[3]/text()').extract_first()
                item['simple_name'] = selector.xpath('./td[1]/a/text()').extract_first()
                item['registe_money'] = selector.xpath('./td[4]/text()').extract_first()
                item['partner_bg'] = selector.xpath('./td[5]/text()').extract_first()
                item['legal_person'] = selector.xpath('./td[6]/text()').extract_first()
                item['address'] = selector.xpath('./td[7]/text()').extract_first()
                item['create_date'] = selector.xpath('./td[8]/text()').extract_first()
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True,meta=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response,**kwargs):
        print(response.meta)
        try:
            item = xtgsItem()
            name = response.xpath('//div[@class="gsxq-table"]/table/tr[2]/td[2]/span/text()').extract_first()
            is_ipo = response.xpath('//div[@class="gsxq-table"]/table/tr[6]/td[4]/span/text()').extract_first()
            dongshizhang = response.xpath('//div[@class="gsxq-table"]/table/tr[4]/td[4]/span/text()').extract_first()
            shareholder = response.xpath('//div[@class="gsxq-table"]/table/tr[6]/td[2]/span/text()').extract_first()
            general_manager = response.xpath('//div[@class="gsxq-table"]/table/tr[5]/td[2]/span/text()').extract_first()
            simple_name = response.meta['simple_name']
            create_date = response.meta['create_date']
            registe_money = response.meta['registe_money']
            address = response.meta['address']
            legal_person = response.meta['legal_person']
            partner_bg = response.meta['partner_bg']
            print(create_date)
            item['name'] = name  # 公司名称
            item['simple_name'] = simple_name  # 公司简称
            item['en_name'] = ''  # 英文名称
            item['create_date'] = get_times(create_date)  # 成立日期
            item['address'] = address  # 所在地
            item['registe_money'] = registe_money  # 注册资本
            item['is_ipo'] = is_ipo  # 是否上市
            item['company_type'] = ''  # 公司类型
            item['regist_address'] = ''  # 注册地址
            item['partner_compose'] = ''  # 股东构成
            item['partner_bg'] = partner_bg  # 股东背景
            item['company_intro'] = ''.join(response.xpath('//p[@class="PD20"]//text()').extract())  # 公司简介
            item['legal_person'] = legal_person  # 法人代表
            item['dongshizhang'] = dongshizhang  # 董事长
            item['shareholder'] = shareholder  # 大股东
            item['general_manager'] = general_manager  # 总经理
            item['aum'] = response.xpath('//div[@class="gsxq_top"]/ul/li[4]/h2/text()').extract_first()  # 资产管理规模
            item['avg_yield'] = response.meta['avg_yield']  # 平均收益率
            item['pro_hold_rate'] = response.meta['pro_hold_rate']   # 产品兑付比例
            item['company_website'] = ''  # 公司网址
            item['telephone'] = ''  # 电话
            item['fax'] = ''  # 传真
            item['postcode'] = ''  # 邮编
            item['website'] = '信托池'  # 数据来源网站
            item['link'] = response.request.url  # 数据源链接
            item['spider_name'] = 'xtgs_xtc'  # 名称
            item['module_name'] = '信托公司_信托池'  # 模块名称

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

