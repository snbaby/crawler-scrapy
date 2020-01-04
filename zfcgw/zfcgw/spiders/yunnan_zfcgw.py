# -*- coding: utf-8 -*-
import scrapy
import logging

from scrapy_splash import SplashRequest
from zfcgw.items import ztbkItem
from utils.tools.attachment import get_attachments,get_times

class YunnanZfcgwSpider(scrapy.Spider):
    name = 'yunnan_zfcgw'
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
        # 'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'SPLASH_URL': "http://39.100.240.19:8050/"}

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
          splash:go(args.url)
          wait_for_element(splash,'#bulletinlistid tbody a')
          splash:runjs("document.querySelector('#bulletinlistid tbody').innerHTML = ''")
          js = string.format("userful('%d')", args.sign)
          splash:evaljs(js)
          wait_for_element(splash,'#bulletinlistid tbody a')
          return splash:html()
        end
        """
        try:
            contents = [
                {
                    'topic': 'cgxx',  # 采购信息
                    'url': 'http://www.ccgp-yunnan.gov.cn/bulletin.do?method=moreList&menuSelect=nav2#'
                }
            ]
            for content in contents:
                signs = [1, 2, 3, 4, 5, 7]
                for sign in signs:
                    yield SplashRequest(content['url'],
                                        endpoint='execute',
                                        args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'sign': sign,
                                        'url': content['url'],
                                        },
                                        callback=self.parse_page,
                                        cb_kwargs={
                                            'url': content['url'],
                                            'topic': content['topic'],
                                            'sign': sign
                    })
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_page(self, response, **kwargs):
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
          splash:go(args.url)
          wait_for_element(splash,'#bulletinlistid tbody a')
          splash:runjs("document.querySelector('#bulletinlistid tbody').innerHTML = ''")
          js = string.format("userful('%d')", args.sign)
          splash:evaljs(js)
          wait_for_element(splash,'#bulletinlistid tbody a')
          splash:runjs("document.querySelector('#bulletinlistid tbody').innerHTML = ''")

          splash:runjs("document.querySelector('.pagination .active').classList.add('test')")
          splash:runjs("document.querySelector('.pagination .test').classList.remove('active')")
          js = string.format("document.querySelector('.pagination .test a').setAttribute('data-page',%d)", args.pagenum)
          splash:evaljs(js)
          splash:runjs("document.querySelector('.pagination .test a').click()")

          wait_for_element(splash, "#bulletinlistid tbody a")
          splash:wait(1)
          return splash:html()
        end
        """

        page_count = int(self.parse_pagenum(response, kwargs))
        try:
            for pagenum in range(page_count):
                url = kwargs['url']
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'pagenum': pagenum + 1,
                                        'sign': kwargs['sign'],
                                        'url': url,
                                    },
                                    callback=self.parse,
                                    cb_kwargs=kwargs)
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse_pagenum(self, response, kwargs):
        try:
            # 在解析页码的方法中判断是否增量爬取并设定爬取列表页数，如果运行
            # 脚本时没有传入参数pagenum指定爬取前几页列表页，则全量爬取
            if not self.add_pagenum:
                total = int(response.css(
                    '.text-default::text').extract_first().split('共')[1].split('条')[0].strip())
                if total / 10 == int(total / 10):
                    return int(total / 10)
                else:
                    return int(total / 10) + 1
            return self.add_pagenum
        except Exception as e:
            logging.error(self.name + ": " + e.__str__())
            logging.exception(e)

    def parse(self, response, **kwargs):
        script = """
        function main(splash, args)
          splash:go(args.url)
          splash:wait(1)
          return splash:html()
        end
        """
        for tr in response.css('#bulletinlistid tbody tr'):
            try:
                title = tr.css('td:nth-child(1)::attr(title)').extract_first()
                time = tr.css('td:nth-child(4)::attr(title)').extract_first()
                region = tr.css('td:nth-child(3)::attr(title)').extract_first()
                bulletin_id = tr.css(
                    'td:nth-child(1) a::attr(data-bulletin_id)').extract_first()
                bulletinclass = tr.css(
                    'td:nth-child(1) a::attr(data-bulletinclass)').extract_first()
                tabletype = tr.css(
                    'td:nth-child(1) a::attr(data-tabletype)').extract_first()
                url = response.urljoin(
                    self.create_url(
                        bulletin_id,
                        bulletinclass,
                        tabletype,
                        kwargs['sign']))
                result = {
                    'title': title,
                    'time': time,
                    'region': region,
                    'url': url
                }
                yield SplashRequest(url,
                                    endpoint='execute',
                                    args={
                                        'lua_source': script,
                                        'wait': 1,
                                        'url': url,
                                    },
                                    callback=self.parse_item,
                                    cb_kwargs=result)
            except Exception as e:
                logging.error(self.name + ": " + e.__str__())
                logging.exception(e)

    def create_url(self, bulletin_id, bulletinclass, tabletype, sign):
        if bulletin_id == "always_show1":
            return '/purchasedetail.do?method=contractList'
        elif sign == 3 or sign == 4:
            if bulletinclass is not None and "" != bulletinclass and "bxlx014" == bulletinclass:
                return "/contract.do?method=showContractDetail&bulletinclass=bxlx014&bulletin_id=" + bulletin_id
            else:
                return "/bulletin_zz.do?method=shownotice&bulletin_id=" + bulletin_id
        elif sign == 5:
            return "/bulletin_zz.do?method=showBulletin&bulletin_id=" + bulletin_id + "&sign=5"
        else:
            return "/bulletin_zz.do?method=showBulletin&bulletin_id=" + \
                bulletin_id + "&bulletinclass=" + bulletinclass

    def parse_item(self, response, **kwargs):
        try:
            appendix, appendix_name = get_attachments(response)
            title = kwargs['title']
            if title.find('招标') >= 0:
                category = '招标'
            elif title.find('中标') >= 0:
                category = '中标'
            elif title.find('成交') >= 0:
                category = '成交'
            elif title.find('结果') >= 0:
                category = '结果'
            elif title.find('单一') >= 0:
                category = '单一'
            else:
                category = '其他'
            item = ztbkItem()
            item['title'] = title
            item['content'] = ''.join(
                response.css('.col-xs-10-sm').extract())
            item['appendix'] = appendix
            item['category'] = category
            item['time'] = kwargs['time']
            item['source'] = ''
            item['website'] = '云南政府采购网'
            item['link'] = kwargs['url']
            item['type'] = '2'
            item['region'] = '云南省'
            item['appendix_name'] = appendix_name
            item['spider_name'] = 'yunnan_zfcgw'
            item['txt'] = ''.join(
                response.css('.col-xs-10-sm *::text').extract())
            item['module_name'] = '云南-政府采购网'
            item['time'] = get_times(item['time'])
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
