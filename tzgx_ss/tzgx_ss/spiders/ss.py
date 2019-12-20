# -*- coding: utf-8 -*-
import scrapy


class SsSpider(scrapy.Spider):
    name = 'ss'
    allowed_domains = ['ss']
    start_urls = ['http://ss/']

    def parse(self, response):
        pass
