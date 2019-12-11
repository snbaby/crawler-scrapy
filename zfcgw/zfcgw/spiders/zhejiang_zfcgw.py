# -*- coding: utf-8 -*-
import scrapy


class ZhejiangZfcgwSpider(scrapy.Spider):
    name = 'zhejiang_zfcgw'
    allowed_domains = ['zhejiang']
    start_urls = ['http://zhejiang/']

    def parse(self, response):
        pass
