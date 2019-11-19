# -*- coding: utf-8 -*-
import scrapy


class XizangSpider(scrapy.Spider):
    name = 'xizang'
    allowed_domains = ['http://www.xizang.gov.cn/']
    start_urls = ['http://http://www.xizang.gov.cn//']

    def parse(self, response):
        pass
