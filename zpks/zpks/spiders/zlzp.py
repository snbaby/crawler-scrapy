# -*- coding: utf-8 -*-
import scrapy
import logging
import time
from scrapy_splash import SplashRequest
from zpks.items import zpksItem
import json
from utils.tools.attachment import get_times

class ZlzpSpider(scrapy.Spider):
    name = 'zlzp'
    custom_settings = {
        'CONCURRENT_REQUESTS': 20,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 1,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://39.100.240.19:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            json_body = {
                "start": 1000,
                "pageSize": "90",
                "workExperience": "-1",
                "education": "-1",
                "companyType": "-1",
                "employmentType": "-1",
                "jobWelfareTag": "-1",
                "kt": "3",
                "at": "cee6a5bb282c45b1a3af0d466af20f18",
                "rt": "093d2b5d43f84f5d885fb6604f6153b8",
                "_v": "0.76340331",
                "userCode": 702162523
            }
            pages = 11
            for j in range(pages):
                json_body['start'] = j*90
                yield scrapy.Request(
                    "https://fe-api.zhaopin.com/c/i/sou?at=cee6a5bb282c45b1a3af0d466af20f18&rt=093d2b5d43f84f5d885fb6604f6153b8&_v=0.53759414&x-zp-page-request-id=2e4b51e656a8495093e59f37dbfcb301-1577207673282-314929&x-zp-client-id=342b4fd1-653a-415e-b3b2-1603acbccdba&MmEwMD=4U.7hI3E_Tkr85QtiHNTgEjtNp1Mv3QpJZ7yE0_1FfCzGHmDHfGMFIhSp3CXIiMnK_gONKotKVTUJthi213Y1ip_RRcLP6VCT2KkLVsKcCv_0dNCSYr8MpjLTbSjVnh_afHeGNWoj.BpFVlKYcqVCTA6Fkg64HXTidPjsuTl5C7kGxP2otzqCyKKMSUdkXKSnMz1qA3O8KtB1S2uzuX6NFfZE5FjSbsx2uvk.6kmbqHzzYUIokJbARH07ozDmd0auk.Fk9cUM5Q18O7pjdj2I6eXqaEKuaFLTU2h5IVaq1U6_RZ08fOfDZf1Yl95IcuVOUfzXzmr6DrsKIL_yHXzf51E99_DSIL_qs.L7fxVlffRDKM4K0G1dN1eF7LvNSx2t0NEeI7vVnfmDXb0QkO1DcgxcJN1cOYXqY4aUVxqXe0Bzz46Ktbqz9NQ5Db.zRtnZoX9",
                    method='POST',
                    headers={'Content-Type': ' application/json;charset=UTF-8'},
                    body=json.dumps(json_body),
                    callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_page(self, response,**kwargs):
        try:
            ret = json.loads(response.text)
            item = zpksItem()
            for obj in ret['data']['results']:
                item['job'] = obj['jobName']
                item['company_name'] = obj['company']['name']
                item['industry'] = obj['jobType']['items'][0]['name']
                item['location'] = obj['city']['display']
                item['salary'] = obj['salary']
                item['time'] = get_times(obj['updateDate'])
                item['link'] = obj['positionURL']
                item['education'] = obj['eduLevel']['name']
                yield scrapy.Request(obj['positionURL'], callback=self.parse_item, dont_filter=True, cb_kwargs=item)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response, **kwargs):
        try:
            kwargs['website'] = '智联招聘'
            kwargs['type'] = '3'
            kwargs['source'] = '智联招聘'
            kwargs['content'] = ''.join(response.xpath('//*[@class="describtion__detail-content"]').extract())
            kwargs['spider_name'] = 'zlzp'
            kwargs['module_name'] = '智联招聘'
            print(
                "===========================>crawled one item" +
                response.request.url)
            yield kwargs
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)