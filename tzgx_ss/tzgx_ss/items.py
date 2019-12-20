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


class tzgx_ssItem(scrapy.Item):
    title = scrapy.Field()
    company_name = scrapy.Field()
    industry = scrapy.Field()
    investors = scrapy.Field()
    time = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    circulation = scrapy.Field()
    code = scrapy.Field()
    supported_vc_pe = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    rotation = scrapy.Field()
    inv_money = scrapy.Field()
    equity_ratio = scrapy.Field()
    inv_value = scrapy.Field()
    content = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
