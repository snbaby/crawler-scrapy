# -*- coding: utf-8 -*-
import scrapy


class GwbzSpider(scrapy.Spider):
    name = 'gwbz'
    allowed_domains = ['gwbz']
    start_urls = ['http://gwbz/']

    def parse(self, response):
        pass
