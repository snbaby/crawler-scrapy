# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import jsonpath
from yxks.items import schoolEssentialLibraryItem,specialtiesInSchoolsItem,recruitPlanLibraryItem,schoolEmploymentLibraryItem,employmentLocalLibraryItem

provinceObject = {
    11: "北京",
    12: "天津",
    13: "河北",
    14: "山西",
    15: "内蒙古",
    21: "辽宁",
    22: "吉林",
    23: "黑龙江",
    31: "上海",
    32: "江苏",
    33: "浙江",
    34: "安徽",
    35: "福建",
    36: "江西",
    37: "山东",
    41: "河南",
    42: "湖北",
    43: "湖南",
    44: "广东",
    45: "广西",
    46: "海南",
    50: "重庆",
    51: "四川",
    52: "贵州",
    53: "云南",
    54: "西藏",
    61: "陕西",
    62: "甘肃",
    63: "青海",
    64: "宁夏",
    65: "新疆",
    71: "香港",
    72: "澳门",
    73: "台湾",
    99: "其它",
    100: "不分省",
    0: "其它"
}
kelei = {
    93: "科类22",
    92: "字段3",
    91: "字段2",
    90: "字段",
    88: "无批次",
    87: "特殊类批",
    86: "本科提前批C段",
    85: "免费师范生批",
    84: "自主招生批",
    83: "专项计划本科二批（贫困专项、南疆单列、对口援疆计划本科二批次）",
    82: "专项计划本科一批（贫困专项、南疆单列、对口援疆计划本科一批次）",
    81: "高校专项批",
    79: "地方专项批",
    76: "提前专项批",
    74: "国家专项批",
    71: "地方农村专项计划本科批",
    70: "本科零批",
    69: "本科综合评价批",
    66: "本科乙批",
    65: "本科甲批",
    64: "地方专项计划本科二批",
    63: "地方专项计划本科一批",
    62: "国家专项计划本科二批",
    61: "国家专项计划本科一批",
    60: "精准脱贫专项计划（专科）",
    59: "精准脱贫专项计划（本科）",
    58: "本科第二批预科B",
    57: "本科第二批预科A",
    56: "本科第一批预科",
    55: "艺术本科第一批专项",
    54: "本科二批C段",
    53: "本科第一批专项",
    52: "本科一批B段",
    51: "本科一批A段",
    50: "单设本科批次",
    49: "专科批B段",
    48: "专科批A段",
    47: "本科批B段",
    46: "本科批A段",
    45: "本科二批B段",
    44: "本科二批A段",
    43: "专项批",
    42: "本科提前批自主招生",
    41: "本科提前一批",
    40: "本科提前二批",
    39: "提前批专项计划",
    38: "普通类平行录取段",
    37: "本科提前批B段",
    36: "本科提前批A段",
    35: "新增批次",
    34: "蒙授艺术",
    33: "蒙授理科",
    32: "蒙授文科",
    31: "蒙授体育",
    30: "民语言艺术类",
    29: "民语言理科",
    28: "民语言文科",
    27: "民语言体育类",
    26: "艺术理",
    25: "艺术文",
    24: "体育理",
    23: "体育文",
    20: "专科二批",
    19: "专科一批",
    18: "平行录取三段",
    17: "平行录取二段",
    16: "平行录取一段",
    15: "普通类提前批",
    14: "本科批",
    13: "地方专项计划本科批",
    12: "国家专项计划本科批",
    11: "专科提前批",
    10: "专科批",
    9: "本科三批",
    8: "本科二批",
    7: "本科一批",
    6: "本科提前批",
    5: "体育类",
    4: "艺术类",
    3: "综合",
    2: "文科",
    1: "理科"
}
class schoolSpider(scrapy.Spider):
    name = 'school'
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
            num = 97
            for i in range(num):
                url = 'https://api.eol.cn/gkcx/api/?access_token=&admissions=&central=&department=&dual_class=&f211=&f985=&is_dual_class=&keyword=&page=' + str(i) + '&province_id=&request_type=1&school_type=&signsafe=&size=30&sort=view_total&type=&uri=apigkcx/api/school/hotlists'
                yield scrapy.Request(url, callback=self.parse_page, dont_filter=True)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response):
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
            school_item['website'] = school['site']
            school_item['major'] = ''
            school_item['sourceWebsite'] = '中国教育在线'
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

            # planUrl = 'https://static-data.eol.cn/www/school/' + str(content['school_id']) + '/dic/specialplan.json'
            # yield scrapy.Request(planUrl, callback=self.parse_plan, dont_filter=True, meta={'name':content['school_id']})

            employmentUrl = 'https://static-data.eol.cn/www/school/' + str(content['school_id']) + '/pc_jobdetail.json'
            yield scrapy.Request(employmentUrl, callback=self.parse_employment, dont_filter=True,
                                 meta={'name': school['name']})
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

    # 招生计划
    def parse_plan(self, response):
        try:
            plans = json.loads(response.text)['data']
            for plan in plans:
                year = plan['year']
                provinces = plan['province']
                for province in provinces:
                    pid = province['pid']
                    types = province['type']
                    batchs = province['batch']
                    for type in types:
                        for batch in batchs:
                            schoolRecruitUrl = 'https://api.eol.cn/gkcx/api/?access_token=&local_batch_id='+str(batch)+'&local_province_id='+str(pid)+'&local_type_id='+str(type)+'&page=1&school_id='+str(response.meta['name'])+'&signsafe=&size=200&uri=apidata/api/gk/plan/special&year='+str(year)
                            print(schoolRecruitUrl)
                            yield scrapy.Request(schoolRecruitUrl, callback=self.parse_plan_item, dont_filter=True,
                                                 meta={'year': year,'province':pid,'type':type})
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_plan_item(self, response):
        try:
            plan_items = json.loads(response.text)['data']['item']
            year = response.meta['year']
            province = response.meta['province']
            type = response.meta['type']
            plan_item = recruitPlanLibraryItem()
            for item in plan_items:
                specialties_item = specialtiesInSchoolsItem()
                plan_item['name'] = item['name']
                plan_item['major'] = item['spname']
                plan_item['secondLevel'] = item['level3_name'] if ('level3_name' in item) else ''
                plan_item['subject'] = item['level2_name']  if ('level2_name' in item) else ''
                plan_item['local'] = provinceObject[province]
                plan_item['majorType'] = kelei[type]
                plan_item['particularYear'] = year
                plan_item['batch'] = item['local_batch_name']
                plan_item['planRecruit'] = item['num']
                plan_item['website'] = ''
                plan_item['link'] = ''
                plan_item['spider_name'] = 'zsjh'
                plan_item['module_name'] = '招生计划'
                plan_item['insert_tpye'] = 'zhaosheng'
                yield plan_item
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    # 就业情况
    def parse_employment(self, response):
        try:
            employment = json.loads(response.text)
            men_rate = jsonpath.jsonpath(employment, '$..men_rate')
            female_rate = jsonpath.jsonpath(employment, '$..female_rate')
            employment_item = schoolEmploymentLibraryItem()
            employment_item['name'] = response.meta['name']
            employment_item['maleRatio'] = men_rate[0] if men_rate!=False else ''
            employment_item['womanRatio'] = female_rate[0] if female_rate!=False else ''
            employment_item['RateOfEmployment'] = employment['jobrate']['job']['1'] if ('jobrate' in employment) and ('job' in employment['jobrate']) and ('1' in employment['jobrate']['job']) else ''
            employment_item['entrance'] = employment['jobrate']['postgraduate']['1']  if ('jobrate' in employment) and ('postgraduate' in employment['jobrate']) and ('1' in employment['jobrate']['postgraduate']) else ''
            employment_item['goingAbroad'] = employment['jobrate']['abroad']['1'] if ('jobrate' in employment) and ('abroad' in employment['jobrate']) and ('1' in employment['jobrate']['abroad']) else ''
            employment_item['website'] = ''
            employment_item['link'] = ''
            employment_item['spider_name'] = 'jyqk'
            employment_item['module_name'] = '就业情况'
            employment_item['insert_tpye'] = 'employment'
            yield employment_item

            employmentLocals = employment['province']
            for employmentLocal in employmentLocals:
                item = employmentLocalLibraryItem()
                item['name'] = response.meta['name']
                item['local'] = employmentLocals[str(employmentLocal)]['province']
                item['proportion'] = employmentLocals[str(employmentLocal)]['rate']
                item['website'] = ''
                item['link'] = ''
                item['spider_name'] = 'jylx'
                item['module_name'] = '就业流向'
                item['insert_tpye'] = 'employment_local'
                yield item
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)