# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
from urllib import parse
from scrapy.item import Field
import scrapy
from scrapy.loader.processors import TakeFirst, MapCompose, Join


class cnki_sbkItem(scrapy.Item):
    title_cn = scrapy.Field()
    financers = scrapy.Field()
    investors = scrapy.Field()
    amount = scrapy.Field()
    rotation = scrapy.Field()
    time = scrapy.Field()
    industry = scrapy.Field()
    introduction = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    content = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
