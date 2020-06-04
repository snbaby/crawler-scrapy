# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy_splash import SplashRequest
from zpks.items import zpksItem
import json
from utils.tools.attachment import get_times

class ZlzpSpider(scrapy.Spider):
    name = 'zlzp1'
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 10,
        'CONCURRENT_REQUESTS_PER_IP': 0,
        'DOWNLOAD_DELAY': 0.5,
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
         'SPLASH_URL': "http://localhost:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            json_body = {
                "pageSize": "90",
                "cityId": "763",
                "workExperience": "-1",
                "education": "-1",
                "companyType": "-1",
                "employmentType": "-1",
                "jobWelfareTag": "-1",
                "kt": "3",
                "at": "5564fca6073a4bb09673c8d5f7398800",
                "rt": "8c9712a650e24e7ba9ff2f1fb1b92048",
                "_v": "0.81047222",
                "userCode": 702162523
            }
            cityList = [
                530,
                538,
                765,
                763,
                531,
                801,
                653,
                600,
                613,
                635,
                702,
                703,
                639,
                599,
                854,
                719,
                749,
                551,
                622,
                636,
                654,
                681,
                682,
                565,
                664,
                773
            ]
            pages = 11
            for city in cityList:
                for j in range(pages):
                    if j>0:
                        json_body['start'] = j*90
                    json_body['cityId'] = str(city)
                    yield scrapy.Request(
                        "https://fe-api.zhaopin.com/c/i/sou?at=5564fca6073a4bb09673c8d5f7398800&rt=8c9712a650e24e7ba9ff2f1fb1b92048&_v=0.93439897&x-zp-page-request-id=54c1684bb3d345f38c5d2b3b826d41ce-1583940312843-772771&x-zp-client-id=342b4fd1-653a-415e-b3b2-1603acbccdba&MmEwMD=50O8oZA_CKhu1wVgc7fo0.Pg2nFN.4VOrI9hlUnGKc5I77J0kcLNKZkkw45QszsqFRap2THgF6e2rNkZNSAv8zREYbAqS_SuJqVJGB.6tC.lvsHCJsaI6oU1yM0yn7Ib7dY_cPuL3Q6lwDzAbOagWUNxqpCoKZMbeQHFGJ6SgnsKMdmrN6JMfpwtQnJX_lcWr.X5398tgA0AKsPXy2vmWk4vlb7JBR.znKxUeFBlCu3NEb_PL73tqOzX4gh5VDgxwyRzkxoKyMwrT5dgmUdVY2khgWQwqYdPQEfeaEkutY.pmuOYensy5O7cqFKhAF4t.V2tUSgn06qzqvZ2YhS5WiPZBx4saTFy4TqE_7mzDfYAtPpAy2hs8CRk1NP9YqJHEIagaqC961ZOWVRipGmc2FZd_qCGVfJ1w0RC0CKYufXLBa8KScWDIHyDPt.MpihxE2bM",
                        method='POST',
                        headers={'Content-Type': 'application/json;charset=UTF-8'},
                        body=json.dumps(json_body),
                        callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_page(self, response):
        print(response.text)
        script = """
        function main(splash, args)
          splash.images_enabled = false
          splash:go(args.url)
          splash:wait(1)
          return splash:html()
        end
        """
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
                # 'https://fe-api.zhaopin.com/c/i/jobs/qrcode?number='+num+'&width=120&hyaline=false&_v=0.36637930&x-zp-page-request-id=996aa803fdd84a87b2a54ebedd8b4992-1577987777991-350633&x-zp-client-id=342b4fd1-653a-415e-b3b2-1603acbccdba'
                print('positionURL:' + str(obj['positionURL']))
                # yield SplashRequest(obj['positionURL'],
                #     endpoint='execute',
                #     args={
                #         'lua_source': script,
                #         'wait': 1,
                #         'url': obj['positionURL'],
                #     },
                #     callback=self.parse_item,
                #     meta=item)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response):
        try:
            response.meta['website'] = '智联招聘'
            response.meta['type'] = '3'
            response.meta['source'] = '智联招聘'
            response.meta['content'] = ''.join(response.xpath('//*[@class="describtion__detail-content"]').extract())
            response.meta['spider_name'] = 'zlzp'
            response.meta['module_name'] = '智联招聘'
            print(
                "===========================>crawled one item" +
                response.request.url)
            yield response.meta
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)