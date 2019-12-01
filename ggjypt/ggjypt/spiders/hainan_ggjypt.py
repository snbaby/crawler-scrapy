# -*- coding: utf-8 -*-
import scrapy


class HainanGgjyptSpider(scrapy.Spider):
    name = 'hainan_ggjypt'
    allowed_domains = ['http://zw.hainan.gov.cn']
    start_urls = ['http://http://zw.hainan.gov.cn/']

    def parse(self, response):
        pass
