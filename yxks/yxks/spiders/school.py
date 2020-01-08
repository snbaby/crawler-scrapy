# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import jsonpath
from yxks.items import schoolEssentialLibraryItem,specialtiesInSchoolsItem,recruitPlanLibraryItem,schoolEmploymentLibraryItem,employmentLocalLibraryItem


class schoolSpider(scrapy.Spider):
    name = 'school'
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
        'SPLASH_URL': 'http://localhost:8050/'}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            num = 2
            for i in range(num):
                url = 'https://api.eol.cn/gkcx/api/?access_token=&admissions=&central=&department=&dual_class=&f211=&f985=&is_dual_class=&keyword=&page=' + str(i) + '&province_id=&request_type=1&school_type=&signsafe=&size=20&sort=view_total&type=&uri=apigkcx/api/school/hotlists'
                print(url)
                yield scrapy.Request(url, callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
        try:
            datas = json.loads(response.text)
            for school in datas['data']['item']:
                infoUrl = 'https://static-data.eol.cn/www/school/'+str(school['school_id'])+'/info.json'
                yield scrapy.Request(infoUrl, callback=self.parse_school, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_school(self, response):
        try:
            school = json.loads(response.text)
            contentUrl = 'https://static-data.eol.cn/www/school/' + str(school['school_id']) + '/detail/69000.json'
            yield scrapy.Request(contentUrl, callback=self.parse_school_content, dont_filter=True,meta=school)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_school_content(self, response):
        try:
            content = json.loads(response.text)
            school = response.meta
            school_item = schoolEssentialLibraryItem()
            school_item['name'] = school['name']
            school_item['type'] = school['type_name']
            school_item['province'] = school['province_name']
            school_item['city'] = school['city_name']
            school_item['education'] = school['level_name']
            school_item['email'] = school['email']
            school_item['phone'] = school['phone']
            school_item['website'] = '中国教育在线'
            school_item['major'] = ''
            school_item['sourceWebsite'] = school['site']
            school_item['link'] = 'https://gkcx.eol.cn/school/' + str(content['school_id'])
            school_item['spider_name'] = 'school'
            school_item['module_name'] = '学校'
            school_item['survey'] = content['content']
            school_item['insert_tpye'] = 'school'
            print(
                "===========================>crawled one item:" + school_item['name'])
            yield school_item
            schoolRpecialtiesUrl = 'https://static-data.eol.cn/www/school/' + str(content['school_id']) + '/pc_special.json'
            yield scrapy.Request(schoolRpecialtiesUrl, callback=self.parse_specialties, dont_filter=True, meta={'name':school['name']})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_specialties(self, response):
        try:
            specialties = json.loads(response.text)
            special_name = jsonpath.jsonpath(specialties, '$..special_name')
            school_name = response.meta['name']
            for name in special_name:
                specialties_item = specialtiesInSchoolsItem()
                specialties_item['school_name'] = school_name
                specialties_item['major'] = name
                specialties_item['insert_tpye'] = 'zhuanye'
                specialties_item['spider_name'] = 'kszy'
                specialties_item['website'] = ''
                specialties_item['link'] = ''
                specialties_item['module_name'] = '开设专业'
                yield specialties_item
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
