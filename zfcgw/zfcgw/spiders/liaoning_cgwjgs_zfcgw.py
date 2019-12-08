# -*- coding: utf-8 -*-
import scrapy


class LiaoningCgwjgsZfcgwSpider(scrapy.Spider):
    name = 'liaoning_cgwjgs_zfcgw'
    allowed_domains = ['www.ccgp-liaoning.gov.cn']
    start_urls = ['http://www.ccgp-liaoning.gov.cn/']

    def parse(self, response):
        pass
