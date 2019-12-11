# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from xtcp.items import xtcpItem

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
    name = 'xtcp_hxsj'
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
            url = "http://data.hexun.com/trust/65.html"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_type)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_type(self, response):
        for href in response.xpath('//div[@class="box stockData mtno"]/table/tr/td/a/@href'):
            try:
                url = response.urljoin(href.extract())
                yield SplashRequest(url,callback=self.parse_page, dont_filter=True,cb_kwargs={'url':url})

            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_page(self, response,**kwargs):
        page_count = int(self.parse_pagenum(response))
        try:
            for pagenum in range(page_count):
                temUrl = kwargs['url'] + '&index=0&order=1&page=' if kwargs['url'].find('fundsinvest') > -1 else kwargs['url'] + '?&investmode=1&index=0&order=1&page='
                url = temUrl + str(pagenum) if pagenum > 0 else kwargs['url']
                yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            return int(response.xpath('//*[@id="pageInfo"]/b/text()').re(r'([1-9]\d*\.?\d*)')[1]) + 1
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for selector in response.xpath('//table[@id="cpcx-result"]/tr'):
            try:
                item = {}
                item['name'] = selector.xpath('./td[3]/a/text()').extract_first()
                item['issure'] = selector.xpath('./td[4]/text()').extract_first()
                item['issue_date'] = selector.xpath('./td[5]/text()').extract_first()
                item['pro_deadline'] = selector.xpath('./td[6]/text()').extract_first()
                item['real_scale'] = selector.xpath('./td[7]/text()').extract_first()
                item['invest_still'] = selector.xpath('./td[8]/text()').extract_first()
                item['invest_method'] = selector.xpath('./td[9]/text()').extract_first()
                item['money_invest'] = selector.xpath('./td[10]/text()').extract_first()
                item['pre_year_income'] = selector.xpath('./td[11]/text()').extract_first()
                url = response.urljoin(selector.xpath('./td[3]/a/@href').extract_first())
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True,cb_kwargs=item)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response,**kwargs):
        if response.text:
            try:

                item = xtcpItem()
                pro_address = response.xpath('//table[@class="jibenxinxi"]/tr[13]/td[4]/text()').extract_first()
                deadline_type = response.xpath('//table[@class="jibenxinxi"]/tr[6]/td[4]/text()').extract_first()
                establish_date = response.xpath('//table[@class="jibenxinxi"]/tr[10]/td[2]/text()').extract_first()
                deadline_date = response.xpath('//table[@class="jibenxinxi"]/tr[2]/td[4]/text()').extract_first()
                pro_state = response.xpath('//table[@class="jibenxinxi"]/tr[2]/td[4]/text()').extract_first()
                pro_type = response.xpath('//table[@class="jibenxinxi"]/tr[2]/td[2]/text()').extract_first()
                money_use = response.xpath('//table[@class="jibenxinxi"]/tr[14]/td[2]/text()').extract_first()
                real_year_income = response.xpath('//table[@class="jibenxinxi"]/tr[7]/td[4]/text()').extract_first()
                income_type = response.xpath('//table[@class="jibenxinxi"]/tr[11]/td[4]/text()').extract_first()

                item['name'] = kwargs['name']
                item['issure'] = kwargs['name']
                item['issue_date'] = kwargs['issue_date']
                item['pro_address'] = pro_address.replace('\xa0','') if pro_address else ''
                item['pre_scale'] = ''
                item['real_scale'] = kwargs['real_scale']
                item['deadline_type'] = deadline_type.replace('\xa0','') if deadline_type else ''
                item['pro_deadline'] = kwargs['pro_deadline']
                item['tj_start_time'] = ''
                item['tj_end_time'] = ''
                item['establish_date'] = establish_date.replace('\xa0','') if establish_date else ''
                item['deadline_date'] = deadline_date.replace('\xa0','') if deadline_date else ''
                item['invest_still'] = kwargs['invest_still']
                item['income_deadline'] = ''
                item['pro_state'] = pro_state.replace('\xa0','') if pro_state else ''
                item['pro_type'] = pro_type.replace('\xa0','') if pro_type else ''
                item['invest_method'] = kwargs['issue_date']
                item['money_invest'] = kwargs['money_invest']
                item['money_use'] = money_use.replace('\xa0','') if money_use else ''
                item['pre_year_income'] = kwargs['pre_year_income']
                item['real_year_income'] = real_year_income.replace('\xa0','') if real_year_income else ''
                item['income_type'] = income_type.replace('\xa0','') if income_type else ''
                item['income_explane'] = ''
                item['pay_method'] = ''
                item['finance_peo'] = ''
                item['risk_method'] = ''
                item['payment'] = ''
                item['pro_highlight'] = ''
                item['pro_plan'] = ''
                item['raise_account'] = ''
                item['money_host_bank'] = ''
                item['asset_manager'] = ''
                item['host_people'] = ''
                item['website'] = '和讯数据'
                item['link'] = response.request.url
                item['spider_name'] = 'xtcp_hxsj'
                item['module_name'] = '信托产品_和讯数据'
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
