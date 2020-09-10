# -*- coding: utf-8 -*-
import scrapy
import logging

from bzk_gjbz.items import bzk_gjbzItem


class DfbzSpider(scrapy.Spider):
    name = 'gjbz'
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        'DOWNLOADER_MIDDLEWARES': {
            # 'scrapy_splash.SplashCookiesMiddleware': 723,
            # 'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        #'SPLASH_URL': "http://localhost:8050/"
        # 'SPLASH_URL': "http://121.36.103.134:8050/"
    }

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        dataList = [
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "11",
                "classname": "医药卫生技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "13",
                "classname": "环保、保健和安全"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "17",
                "classname": "计量学和测量、物理现象"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "19",
                "classname": "试验"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "21",
                "classname": "机械系统和通用件"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "23",
                "classname": "流体系统和通用件"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "25",
                "classname": "机械制造"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "27",
                "classname": "能源和热传导工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "29",
                "classname": "电气工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "31",
                "classname": "电子学"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "33",
                "classname": "电信、音频和视频工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "35",
                "classname": "信息技术、办公机械"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "37",
                "classname": "成像技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "39",
                "classname": "精密机械、珠宝"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "43",
                "classname": "道路车辆工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "45",
                "classname": "铁路工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "47",
                "classname": "造船和海上构筑物"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "49",
                "classname": "航空器和航天器工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "53",
                "classname": "材料储运设备"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "55",
                "classname": "货物的包装和调运"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "59",
                "classname": "纺织和皮革技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "61",
                "classname": "服装工业"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "65",
                "classname": "农业"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "67",
                "classname": "食品技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "71",
                "classname": "化工技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "73",
                "classname": "采矿和矿产品"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "75",
                "classname": "石油及相关技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "77",
                "classname": "冶金"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "79",
                "classname": "木材技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "81",
                "classname": "玻璃和陶瓷工业"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "83",
                "classname": "橡胶和塑料工业"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "85",
                "classname": "造纸技术"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "87",
                "classname": "涂料和颜料工业"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "91",
                "classname": "建筑材料和建筑物"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "93",
                "classname": "土木工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "95",
                "classname": "军事工程"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "97",
                "classname": "家用和商用设备、文娱、体育"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "01",
                "classname": "综合、术语学、标准化、文献"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "03",
                "classname": "社会学、服务、公司(企业)的组织和管理、行政、运输"
            },
            {
                "pageIndex": "1",
                "standclass": "ISO",
                "classcode": "07",
                "classname": "数学、自然科学"
            }
        ]
        try:
            for data in dataList:
                for i in range(30):
                    yield scrapy.FormRequest('https://www.spc.org.cn/basicsearch', formdata={
                        'pageIndex': str(i + 1),
                        'standclass': data['standclass'],
                        'classcode': data['classcode'],
                        'classname': data['classname'],
                    }, callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

        # yield scrapy.Request('https://www.spc.org.cn/online/ISO%2520266%253A1997%2520EN/?', callback=self.parse_item, dont_filter=True,
        #                      priority=10)
    def parse_page(self, response):
        result = response.text.split('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
        res = scrapy.Selector(text=result[2])
        try:
            for item in res.css('div.titleft a:nth-child(1) span::attr(title)').extract():
                url = 'https://www.spc.org.cn/online/' + str(item)
                print(url)
                yield scrapy.Request(url, callback=self.parse_item, dont_filter=True,
                                     priority=10)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response):
        result = response.text.split(
            '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">')
        res = scrapy.Selector(text=result[1])
        try:
            item = bzk_gjbzItem()
            item['name'] = res.css('#standard_name::text').extract_first()
            item['code'] = res.css('#standard_code::text').extract_first()
            item['status'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(1) > ul > li:nth-child(4) > span::text').extract_first()
            item['committees'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(6) > ul > li:nth-child(6) > span::text').extract_first()
            item['approvalDate'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(1) > ul > li:nth-child(5) > span::text').extract_first()
            item['implementationDate'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(1) > ul > li:nth-child(6) > span::text').extract_first()
            item['sourceWebsite'] = '中国标准在线服务网'
            item['ics'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(2) > ul > li:nth-child(1) > span::text').extract_first()
            item['pub_lang'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(1) > ul > li:nth-child(7) > span::text').extract_first()
            item['pub_organization'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(6) > ul > li:nth-child(8) > span::text').extract_first()
            item['replace'] = res.css("#a461::text").extract_first()
            item['replaced'] = res.css("#a461::text").extract_first()
            item['dept_host'] = res.css(
                '#content > div.detailedinfo-main > div:nth-child(6) > ul > li:nth-child(8) > span::text').extract_first()
            item['scope'] = res.css(
                '#content > div.detailedinfo-top > div.stand-detail-description > div.detailedinfo-text::text').extract_first()
            item['link'] = response.request.url
            item['module_name'] = '标准库-国际标准'
            item['spider_name'] = 'gjbz'
            print("===========================>crawled one item" + response.request.url)
            yield item
        except Exception as e:
            logging.error(self.name + " in parse_item: url=" + response.request.url + ", exception=" + e.__str__())
            logging.exception(e)
