# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy_splash import SplashRequest
from zpks.items import zpksItem
import json
from utils.tools.attachment import get_times

class ZlzpSpider(scrapy.Spider):
    name = 'zlzp'
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
        'SPLASH_URL': "http://47.106.239.73:8050/"}

    def __init__(self, pagenum=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_pagenum = pagenum

    def start_requests(self):
        try:
            json_body = {
                "pageSize": "90",
                "cityId": "801",
                "workExperience": "-1",
                "education": "-1",
                "companyType": "-1",
                "employmentType": "-1",
                "jobWelfareTag": "-1",
                "kt": "3",
                "at": "3e24e15426604d72a964d28f7d1228a3",
                "rt": "a48e54219dc847399c1cbdeb41907156",
                "_v": "0.32762194",
                "userCode": 1055007456
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
                        "https://fe-api.zhaopin.com/c/i/sou?at=3e24e15426604d72a964d28f7d1228a3&rt=a48e54219dc847399c1cbdeb41907156&_v=0.31682191&x-zp-page-request-id=d24b8e8d045340c180b5d617ebae39e3-1578154614610-240921&x-zp-client-id=342b4fd1-653a-415e-b3b2-1603acbccdba&MmEwMD=4L0MCGodotQCOrkeuaCcm6TeVXJ7FvkbakuiTh22v8NFwaFSn8d7vGVD7vNRPSlm.mvVVN3e..jGaTVy3zoPBSiJ9WK3ugRau7NQ7w9QcW2_ortWDEMQjYv2fpzGRQ3DthIe9U0w3VyzEqoJU0lbqbHotVKDGP2vHQvxf5RrTMEIMop6lrKrURB0dbS5Bl7NDNH39oZC7CWT8K.FQ9kgPykqeIkmGCwqPRJhapj2K.tCyNwtkUVF_5grwVrm2nc4HKAGx5GA4_HqlSdZraMtabW4QO1KoY.jziRyWTT7P27ygBuYo.N19tfOlBtCprpNVXBywhoxyUz4DX1tWXp6rBb8VRt.xd3SOGQB3PqYhH8RvpEsSCTPU7N_zIiTpJjajjGQICvQ1ZTPWImEMBU06ybqzlm3zPIogsBcWuCj53A6uMYg_B6cStBsqxGSdDIielgK",
                        method='POST',
                        headers={'Content-Type': ' application/json;charset=UTF-8'},
                        body=json.dumps(json_body),
                        callback=self.parse_page)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)
    def parse_page(self, response,**kwargs):
        print('aaaaaaaaaaaaaaaaaaa')
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
                print(obj['positionURL'])
                yield SplashRequest(obj['positionURL'],
                    endpoint='execute',
                    args={
                        'lua_source': script,
                        'wait': 1,
                        'url': obj['positionURL'],
                    },
                    callback=self.parse_item,
                    cb_kwargs=item)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_item(self, response, **kwargs):
        print(response.text)
        try:
            kwargs['website'] = '智联招聘'
            kwargs['type'] = '3'
            kwargs['source'] = '智联招聘'
            print(response.xpath('//*[@class="describtion__detail-content"]').extract())
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