# -*- coding: utf-8 -*-
import scrapy


class FlfgSpider(scrapy.Spider):
    name = 'flfg'
    allowed_domains = ['flfg']
    start_urls = ['http://flfg/']

    def parse(self, response):
        pass
