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

class tzgx_bgItem(scrapy.Item):
    title = scrapy.Field()
    acquirer = scrapy.Field()
    acquirerd = scrapy.Field()
    status = scrapy.Field()
    industry = scrapy.Field()
    involving_equity = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    supported_vc_pe = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    content = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
