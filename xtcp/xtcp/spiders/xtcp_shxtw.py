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
    name = 'xtcp_shxtw'
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
            url = "http://www.shxtw.net/product/xtcp/"
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
                    url = 'http://www.shxtw.net/product/xtcp/list_10_'+str(pagenum)+'.html' if pagenum > 1 else "http://www.shxtw.net/product/xtcp/"
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//*[@class="pageinfo"]/strong[1]/text()').extract_first()) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//a[@class="tpl-item-title fl"]/@href').extract():
            try:
                url = response.urljoin(href)
                print(url)
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        try:
            item = xtcpItem()
            name = response.xpath('//div[@class="productname"]/h1/text()').extract_first()
            issure = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[2]/td[2]/text()').extract_first()
            issue_date = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[2]/td[4]/text()').extract_first()
            real_scale = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[5]/td[2]/text()').extract_first()
            pro_deadline = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[3]/td[2]/text()').extract_first()
            invest_still = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[5]/td[4]/text()').extract_first()
            income_deadline = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[3]/td[4]/text()').extract_first()
            pro_state = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[1]/td[4]/text()').extract_first()
            pro_type = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[4]/td[2]/text()').extract_first()
            money_invest = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[4]/td[4]/text()').extract_first()
            money_use = response.xpath('//div[@class="p-b-25"]/table/tr[3]/td[2]/span/text()').extract_first()
            pre_year_income = response.xpath('//div[@class="productname"]/p[2]//span/text()').extract_first()
            pay_method = response.xpath('//div[@class="clearfix p-b-25"]/table/tr[3]/td[4]/text()').extract_first()
            risk_method = response.xpath('//div[@class="p-b-25"]/table/tr[5]/td[2]/span/text()').extract_first()
            payment = response.xpath('//div[@class="p-b-25"]/table/tr[4]/td[2]/span/text()').extract_first()
            finance_peo = response.xpath('//div[@class="p-b-25"]/table/tr[2]/td[2]/span/text()').extract_first()
            pro_highlight = ''.join(response.xpath('//div[@class="p-b-25"]/table/tr[6]/td[2]/span//text()').extract())
            raise_account = ''.join(response.xpath('//div[@class="p-b-25"]/table/tr[1]/td[2]/span//text()').extract())

            item['name'] = name  # 产品名称
            item['issure'] = issure  # 发行机构
            item['issue_date'] = issue_date  # 发行时间
            item['pro_address'] = ''  # 项目所在地
            item['pre_scale'] = ''  # 预期发行规模
            item['real_scale'] = real_scale  # 实际发行规模
            item['deadline_type'] = ''  # 期限类型
            item['pro_deadline'] = pro_deadline  # 产品期限
            item['tj_start_time'] = ''  # 推介起始日
            item['tj_end_time'] = ''  # 推介截止日
            item['establish_date'] = ''  # 成立日期
            item['deadline_date'] = ''  # 截止日期
            item['invest_still'] = invest_still  # 投资门槛
            item['income_deadline'] = income_deadline  # 收益期限
            item['pro_state'] = pro_state  # 产品状态
            item['pro_type'] = pro_type.replace('\xa0', '') if pro_type else ''  # 产品类型
            item['invest_method'] = ''  # 投资方式
            item['money_invest'] = money_invest  # 资金投向
            item['money_use'] = money_use.replace('\xa0', '') if money_use else ''  # 资金运用
            item['pre_year_income'] = pre_year_income  # 预期年收益率
            item['real_year_income'] = ''  # 实际年收益率
            item['income_type'] = ''  # 收益类型
            item['income_explane'] = ''  # 收益说明
            item['pay_method'] = pay_method  # 付息方式
            item['finance_peo'] = finance_peo  # 融资方
            item['risk_method'] = risk_method  # 风险控制
            item['payment'] = payment  # 还款来源
            item['pro_highlight'] = pro_highlight  # 项目亮点
            item['pro_plan'] = ''  # 项目进度
            item['raise_account'] = raise_account.replace('\xa0', '') if raise_account else ''  # 募集账号
            item['money_host_bank'] = ''  # 资金托管行
            item['asset_manager'] = ''  # 资产管理人
            item['host_people'] = ''  # 托管人
            item['website'] = '上海信托网'  # 数据来源网站
            item['link'] = response.request.url  # 数据源链接
            item['spider_name'] = 'xtcp_shxtw'  # 名称
            item['module_name'] = '信托产品_上海信托网'  # 模块名称
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

