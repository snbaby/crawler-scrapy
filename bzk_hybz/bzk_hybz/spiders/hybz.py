# -*- coding: utf-8 -*-
import scrapy


class HybzSpider(scrapy.Spider):
    name = 'hybz'
    allowed_domains = ['hybz']
    start_urls = ['http://hybz/']

    def parse(self, response):
        pass
