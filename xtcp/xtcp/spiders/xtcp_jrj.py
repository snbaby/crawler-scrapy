# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import time

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
    name = 'xtcp_jrj'
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
            url = "http://trust.jrj.com/json/p.jspa?size=2000&pn=0&t={%22prd_status%22:%22%22,%22inv_fld%22:%22%22,%22trust_type%22:%22%22,%22trust_peri%22:%22%22,%22exp_yld%22:%22%22,%22min_cap%22:%22%22,%22orgcode%22:%22%22,%22trust_name%22:%22%22,%22order%22:%22desc%22,%22sort%22:%22enddate%22}&run=0.9985752275784832&_=1576253875459"
            yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        dataStr = response.text.replace('var content=','')
        data = json.loads(dataStr)
        page_count = int(self.parse_pagenum(data))
        print(page_count)
        try:
            for pagenum in range(page_count):
                if pagenum > 0:
                    url = "http://trust.jrj.com/json/p.jspa?size=2000&pn="+str(pagenum)+"&t={%22prd_status%22:%22%22,%22inv_fld%22:%22%22,%22trust_type%22:%22%22,%22trust_peri%22:%22%22,%22exp_yld%22:%22%22,%22min_cap%22:%22%22,%22orgcode%22:%22%22,%22trust_name%22:%22%22,%22order%22:%22desc%22,%22sort%22:%22enddate%22}&run=0.9985752275784832&_=1576253875459"
                    yield SplashRequest(url, args={'lua_source': script, 'wait': 1}, callback=self.parse, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                return int(response['page']['pagesize']) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        dataStr = response.text.replace('var content=', '')
        data = json.loads(dataStr)
        for obj in data['trustProductList']:
            try:
                url = 'http://trust.jrj.com/json/d.jspa?innercode='+str(obj['innerCode']+'&_=1576256634483')
                yield SplashRequest(url,callback=self.parse_item, dont_filter=True)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)
        # 处理翻页
        # 1. 获取翻页链接
        # 2. yield scrapy.Request(第二页链接, callback=self.parse, dont_filter=True)

    def parse_item(self, response):
        dataStr = response.text.replace('var content=', '')
        jsonData = json.loads(dataStr)
        if ('trustProductDetail' in jsonData) :
            detail = json.loads(dataStr)['trustProductDetail']
            try:
                item = xtcpItem()
                name = detail['trustSName']
                issure = detail['orgName']
                issue_date = detail['buildDate']
                establish_date = detail['buildDate']
                pro_address = detail['provName']
                real_scale = detail['issSize']
                pro_deadline = detail['trustPeri']
                deadline_date = detail['endDate']
                invest_still = detail['minCap']
                tj_start_time = detail['promStartDate']
                tj_end_time = detail['promEndDate']
                pro_state = detail['prdStatus']
                pro_type = detail['trustType']
                money_invest = detail['invFld']
                money_use = detail['investRemark']
                pre_year_income = detail['expYld']
                income_type = detail['incomeType']
                income_explane = detail['expYldRemark']
                risk_method = detail['credEnhaMode']


                item['name'] = name  # 产品名称
                item['issure'] = issure  # 发行机构
                item['issue_date'] = get_times(issue_date)  # 发行时间
                item['pro_address'] = pro_address  # 项目所在地
                item['pre_scale'] = ''  # 预期发行规模
                item['real_scale'] = real_scale  # 实际发行规模
                item['deadline_type'] = ''  # 期限类型
                item['pro_deadline'] = pro_deadline  # 产品期限
                item['tj_start_time'] = get_times(tj_start_time)  # 推介起始日
                item['tj_end_time'] = get_times(tj_end_time)  # 推介截止日
                item['establish_date'] = get_times(establish_date)  # 成立日期
                item['deadline_date'] =get_times(deadline_date)  # 截止日期
                item['invest_still'] = invest_still  # 投资门槛
                item['income_deadline'] = ''  # 收益期限
                item['pro_state'] = pro_state  # 产品状态
                item['pro_type'] = pro_type.replace('\xa0', '') if pro_type else ''  # 产品类型
                item['invest_method'] = ''  # 投资方式
                item['money_invest'] = money_invest  # 资金投向
                item['money_use'] = money_use.replace('\xa0', '') if money_use else ''  # 资金运用
                item['pre_year_income'] = pre_year_income  # 预期年收益率
                item['real_year_income'] = ''  # 实际年收益率
                item['income_type'] = income_type  # 收益类型
                item['income_explane'] = income_explane  # 收益说明
                item['pay_method'] = ''  # 付息方式
                item['finance_peo'] = ''  # 融资方
                item['risk_method'] = risk_method  # 风险控制
                item['payment'] = ''  # 还款来源
                item['pro_highlight'] = ''  # 项目亮点
                item['pro_plan'] = ''  # 项目进度
                item['raise_account'] = ''  # 募集账号
                item['money_host_bank'] = ''  # 资金托管行
                item['asset_manager'] = ''  # 资产管理人
                item['host_people'] = ''  # 托管人
                item['website'] = '金融界'  # 数据来源网站
                item['link'] = response.request.url  # 数据源链接
                item['spider_name'] = 'xtcp_jrj'  # 名称
                item['module_name'] = '信托产品_金融界'  # 模块名称
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
        else:
            print('dataStr====' + dataStr)

