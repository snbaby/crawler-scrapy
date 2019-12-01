# -*- coding: utf-8 -*-
import scrapy


class QinghaiGgjyptSpider(scrapy.Spider):
    name = 'qinghai_ggjypt'
    allowed_domains = ['http://www.qhggzyjy.gov.cn']
    start_urls = ['http://http://www.qhggzyjy.gov.cn/']

    def parse(self, response):
        pass
