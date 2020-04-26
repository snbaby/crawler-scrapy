# -*- coding: utf-8 -*-
import scrapy
import logging
import json
from yxks.items import majorInfoLibraryItem,majorLocalLibraryItem,majorObtainLibraryItem,schoolInMajorItem

class schoolSpider(scrapy.Spider):
    name = 'major'
    custom_settings = {
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.25,
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DOWNLOADER_MIDDLEWARES': {
            # 'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
            'utils.middlewares.ProxyMiddleWare.ProxyMiddleWare': 110,
            'utils.middlewares.MyUserAgentMiddleware.MyUserAgentMiddleware': 126,
            'utils.middlewares.DeduplicateMiddleware.DeduplicateMiddleware': 130,
            # 'yxks.utils.middleware.ProxyMiddleWare.ProxyMiddleWare': 100,
            # 'scrapy.downloadermiddleware.httpproxy.HttpProxyMiddleware': 700,
        },
        'ITEM_PIPELINES': {
            'utils.pipelines.MysqlTwistedPipeline.MysqlTwistedPipeline': 64,
            'utils.pipelines.DuplicatesPipeline.DuplicatesPipeline': 100,
        }
    }

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            num = 50
            for i in range(num):
                url = 'https://api.eol.cn/gkcx/api/?access_token=&page='+str(i)+'&signsafe=&size=30&uri=apidata/api/gk/special/lists&keyword=&level1=&level2='
                yield scrapy.Request(url, callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
        try:
            datas = json.loads(response.text)
            if len(datas['data']['item']) > 0:
                for major in datas['data']['item']:
                    majorInfoUrl = 'https://static-data.eol.cn/www/special/'+str(major['special_id'])+'/pc_special_detail.json';
                    majorHeatUrl = 'https://api.eol.cn/gkcx/api/?access_token=&signsafe=&special_id='+str(major['special_id'])+'&uri=apidata/api/gk/special/heat'
                    majorInSchoolUrl = 'https://api.eol.cn/gkcx/api/?access_token=&keyword=&page=1&province_id=&request_type=1&school_type=&signsafe=&size=30&special_id='+str(major['special_id'])+'&type=&uri=apidata/api/gk/schoolSpecial/lists'
                    major['majorInfoUrl'] = majorInfoUrl
                    yield scrapy.Request(majorHeatUrl, callback=self.parse_major, dont_filter=True,meta=major)
                    yield scrapy.Request(majorInSchoolUrl, callback=self.school_page, dont_filter=True,meta=major)

        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_major(self, response):
        try:
            majorHeat = json.loads(response.text)
            majorHeat['level2_name'] = response.meta['level2_name']
            yield scrapy.Request(response.meta['majorInfoUrl'], callback=self.parse_major_info, dont_filter=True,meta=majorHeat)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_major_info(self, response):
        try:
            majorHeat = response.meta
            majorInfo = json.loads(response.text)
            item = majorInfoLibraryItem()
            item['majorName'] = majorInfo['name']
            item['majorCode'] = majorInfo['code']
            item['majorPopularity'] = majorHeat['data']['view_total']
            item['AcademicDegree'] = majorInfo['degree']
            item['studyYear'] = majorInfo['limit_year']
            item['subjectType'] = majorHeat['level2_name']
            item['majorType'] = majorInfo['type_detail']
            item['arrangement'] = majorInfo['level1_name']
            maleRatio = majorInfo['rate']
            list = maleRatio.split(':')
            item['maleRatio'] = list[0] if len(list) > 0 else ''
            item['womanRatio'] = list[1] if len(list) > 1 else ''
            detail = ''
            if majorInfo['job'] is None:
                print('job is null')
            else:
                detail = detail + majorInfo['job']
            if majorInfo['content'] is None:
                print('content is null')
            else:
                detail = detail + majorInfo['content']
            selector = scrapy.Selector(text=detail)
            txt = ''.join(selector.xpath('.//text()').extract())
            item['detail'] = detail
            item['FirstImpression'] = json.dumps(majorInfo['impress'])
            item['sourceWebsite'] = '高考数据查询'
            item['link'] = 'https://gkcx.eol.cn/special/'+str(majorInfo['id'])
            item['txt'] = txt
            item['spider_name'] = 'jbxx'
            item['module_name'] = '基本信息'
            item['insert_tpye'] = 'major_info_library'
            print(
                "===========================>crawled one item:" + majorInfo['name'])
            yield item
            if ('jobdetail' in majorInfo) and ('2' in majorInfo['jobdetail']):
                for local in majorInfo['jobdetail']['2']:
                    major_local = majorLocalLibraryItem()
                    major_local['majorName'] = majorInfo['name']
                    major_local['majorCode'] = majorInfo['code']
                    major_local['local'] = local['area']
                    major_local['proportion'] = local['rate']
                    major_local['spider_name'] = 'dqfb'
                    major_local['module_name'] = '就业地区分布'
                    major_local['insert_tpye'] = 'major_local_library'
                    yield major_local

            if ('jobrate' in majorInfo):
                for jobrate in majorInfo['jobrate']:
                    major_obtain = majorObtainLibraryItem()
                    major_obtain['majorName'] = majorInfo['name']
                    major_obtain['majorCode'] = majorInfo['code']
                    major_obtain['particularYear'] = jobrate['year']
                    major_obtain['rateOfEmployment'] = jobrate['rate']
                    major_obtain['spider_name'] = 'jyl'
                    major_obtain['module_name'] = '就业率'
                    major_obtain['insert_tpye'] = 'major_obtain_library'
                    yield major_obtain
        except Exception as e:
            logging.error(majorInfo['name'] + ": " + e.__str__())
            logging.exception(e)

    def school_page(self,response):
        numFound = int(json.loads(response.text)['data']['numFound'])
        if numFound > 0:
            page = int(numFound // 30) + 1
            for num in range(page):
                majorInSchoolUrl = 'https://api.eol.cn/gkcx/api/?access_token=&keyword=&page='+str(num)+'&province_id=&request_type=1&school_type=&signsafe=&size=30&special_id=' + str(
                    response.meta['special_id']) + '&type=&uri=apidata/api/gk/schoolSpecial/lists'
                yield scrapy.Request(majorInSchoolUrl, callback=self.school_item, dont_filter=True)

    def school_item(self,response):
        list = json.loads(response.text)['data']['item']
        if len(list)>0:
            for school in list:
                school_item = schoolInMajorItem()
                school_item['major_name'] = school['spname']
                school_item['colleges_name'] = school['name']
                school_item['spider_name'] = 'ksyx'
                school_item['module_name'] = '开设院校'
                school_item['insert_tpye'] = 'school_in_major'
                yield school_item

