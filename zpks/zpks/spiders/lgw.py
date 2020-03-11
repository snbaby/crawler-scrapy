# -*- coding: utf-8 -*-
import scrapy
import logging
import time
import datetime
from scrapy_splash import SplashRequest
from zpks.items import zpksItem


class LgwSpider(scrapy.Spider):
    name = 'lgw'
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
        script = """
                function wait_for_element(splash, css, maxwait)
                  -- Wait until a selector matches an element
                  -- in the page. Return an error if waited more
                  -- than maxwait seconds.
                  if maxwait == nil then
                      maxwait = 10
                  end
                  return splash:wait_for_resume(string.format([[
                    function main(splash) {
                      var selector = '%s';
                      var maxwait = %s;
                      var end = Date.now() + maxwait*1000;

                      function check() {
                        if(document.querySelector(selector)) {
                          splash.resume('Element found');
                        } else if(Date.now() >= end) {
                          var err = 'Timeout waiting for element';
                          splash.error(err + " " + selector);
                        } else {
                          setTimeout(check, 200);
                        }
                      }
                      check();
                    }
                  ]], css, maxwait))
                end
                function main(splash, args)
                  splash.images_enabled = false
                  splash:go(args.url)
                  wait_for_element(splash,'.s_position_list ul.item_con_list li')
                  splash:runjs("document.querySelector('.s_position_list ul.item_con_list').innerHTML = ''")
                  splash:runjs("document.querySelector('#s_position_list > div.item_con_pager > div > span:nth-child(2)').classList.remove('pager_is_current')")
                  splash:wait(1)
                  splash:runjs("document.querySelector('#s_position_list > div.item_con_pager > div > span:nth-child(2)').classList.add('pager_not_current')")
                  splash:wait(1)
                  js = string.format("document.querySelector('#s_position_list > div.item_con_pager > div > span:nth-child(2)').setAttribute('page',%d)", args.pagenum)
                  splash:evaljs(js)
                  splash:runjs("document.querySelector('#s_position_list > div.item_con_pager > div > span:nth-child(2)').click()")
                  wait_for_element(splash,'.s_position_list ul.item_con_list li')
                  splash:wait(1)
                  return splash:html()
                end
                """
        try:
            contents = [
                {
                    'topic': 'lgw',  # 采购公告
                    'url': 'https://www.lagou.com/jobs/list_?labelWords=&fromSearch=true&suginput='
                }
            ]
            for content in contents:
                page_count = 30
                for pagenum in range(page_count):
                    yield SplashRequest(content['url'],
                                        endpoint='execute',
                                        args={
                                            'lua_source': script,
                                            'wait': 1,
                                            'pagenum': pagenum + 1,
                                            'url': content['url'],
                                        },
                                        callback=self.parse)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response):
        script = """
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(1))
          return {
            html = splash:html(),
          }
        end
        """
        for href in response.xpath('//a[@class="position_link"]/@href').extract():
            try:
                yield SplashRequest(href,
                    endpoint='execute',
                    args={
                        'lua_source': script,
                        'wait': 1,
                        'url': href,
                    },
                    callback=self.parse_item,
                    meta={'url':href})
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def parse_item(self, response):
        try:
            print(response.xpath('/html/body/div[6]/div/div[1]/div/h1/text()'))
            if response.xpath('/html/body/div[6]/div/div[1]/div/h1/text()'):
                print('url===' + str(response.meta['url']))
                item = zpksItem()
                item['job'] = response.xpath('/html/body/div[6]/div/div[1]/div/h1/text()').extract_first()
                company_name = response.xpath('//em[@class="fl-cn"]/text()').extract_first()
                item['company_name'] = company_name.strip() if company_name else ''
                item['industry'] = ''.join(response.xpath('//ul[@class="position-label clearfix"]/li/text()').extract())
                location = ''.join(response.xpath('//div[@class="work_addr"]/a/text()').extract())
                item['location'] = location.replace('查看地图', '') if location else ''
                item['salary'] = response.xpath('//*[@class="salary"]/text()').extract_first()
                item['time'] = datetime.date.today()
                item['website'] = '拉勾网'
                item['link'] = response.meta['url']
                item['type'] = '4'
                item['source'] = '拉勾网'
                item['content'] = ''.join(response.xpath('//*[@class="job-detail"]').extract())
                print(response.xpath('//dd[@class="job_request"]/h3/span[4]').extract_first())
                education = response.xpath('//dd[@class="job_request"]/h3/span[4]/text()').extract_first()
                item['education'] = education.replace('/','') if education else ''
                item['spider_name'] = 'lgw'
                item['module_name'] = '拉勾网'
                print(
                    "===========================>crawled one item" +
                    response.request.url)
                yield item
        except Exception as e:
            logging.error(
                self.name +
                " in parse_item: url=" +
                response.request.url +
                ", exception=" +
                e.__str__())
            logging.exception(e)