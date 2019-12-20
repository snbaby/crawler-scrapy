# -*- coding: utf-8 -*-
import scrapy


class TzrSpider(scrapy.Spider):
    name = 'tzr'
    allowed_domains = ['tzr']
    start_urls = ['http://tzr/']

    def parse(self, response):
        pass
