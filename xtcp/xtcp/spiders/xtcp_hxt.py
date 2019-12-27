# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from xtcp.items import xtcpItem
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
    name = 'xtcp_hxt'
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
            url = "http://www2.haoxintuo.com/index.php?a=lists&catid=34&status=all&page=1"
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
                    url = 'http://www2.haoxintuo.com/index.php?a=lists&catid=34&status=all&page=' + str(pagenum)
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response.xpath('//*[@class="pager"]/a[last()]/@href').re(r'([1-9]\d*\.?\d*)')[2]) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        for href in response.xpath('//a[@class="tt"]/@href').extract():
            try:
                print(response.urljoin(href))
                yield SplashRequest(response.urljoin(href),callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response,**kwargs):
        logging.error(response.text)
        try:
            item = xtcpItem()
            name = response.xpath('//div[@class="productgk"]/table/tr[1]/td[2]/text()').extract_first()


            item['name'] = name  # 产品名称
            item['issure'] = issure  # 发行机构
            item['issue_date'] = '' # 发行时间
            item['pro_address'] = ''  # 项目所在地
            item['pre_scale'] = ''  # 预期发行规模
            item['real_scale'] = real_scale  # 实际发行规模
            item['deadline_type'] = ''  # 期限类型
            item['pro_deadline'] = pro_deadline  # 产品期限
            item['tj_start_time'] = ''  # 推介起始日
            item['tj_end_time'] = ''  # 推介截止日
            item['establish_date'] = '' # 成立日期
            item['deadline_date'] = ''  # 截止日期
            item['invest_still'] = invest_still  # 投资门槛
            item['income_deadline'] = ''  # 收益期限
            item['pro_state'] = pro_state.replace('\xa0','') if pro_state else ''  # 产品状态
            item['pro_type'] = '信托产品'  # 产品类型
            item['invest_method'] = ''  # 投资方式
            item['money_invest'] = money_invest  # 资金投向
            item['money_use'] = ''  # 资金运用
            item['pre_year_income'] = pre_year_income  # 预期年收益率
            item['real_year_income'] = ''  # 实际年收益率
            item['income_type'] = ''  # 收益类型
            item['income_explane'] = ''  # 收益说明
            item['pay_method'] = pay_method  # 付息方式
            item['finance_peo'] = finance_peo  # 融资方
            item['risk_method'] = risk_method.replace('\xa0','') if risk_method else ''  # 风险控制
            item['payment'] = payment.replace('\xa0','') if payment else ''  # 还款来源
            item['pro_highlight'] = pro_highlight  # 项目亮点
            item['pro_plan'] = pro_plan  # 项目进度
            item['raise_account'] = ''  # 募集账号
            item['money_host_bank'] = ''  # 资金托管行
            item['asset_manager'] = ''  # 资产管理人
            item['host_people'] = ''  # 托管人
            item['website'] = '好信托'  # 数据来源网站
            item['link'] = response.request.url  # 数据源链接
            item['spider_name'] = 'xtcp_hxt'  # 名称
            item['module_name'] = '信托产品_好信托'  # 模块名称
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

