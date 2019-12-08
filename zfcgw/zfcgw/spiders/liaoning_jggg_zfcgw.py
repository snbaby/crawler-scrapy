# -*- coding: utf-8 -*-
import scrapy


class LiaoningJgggZfcgwSpider(scrapy.Spider):
    name = 'liaoning_jggg_zfcgw'
    allowed_domains = ['www.ccgp-liaoning.gov.cn']
    start_urls = ['http://www.ccgp-liaoning.gov.cn/']

    def parse(self, response):
        pass
