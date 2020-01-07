# -*- coding: utf-8 -*-
import scrapy


class GnbzSpider(scrapy.Spider):
    name = 'gnbz'
    allowed_domains = ['gnbz']
    start_urls = ['http://gnbz/']

    def parse(self, response):
        pass
