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


class cnki_flfgItem(scrapy.Item):
    title = scrapy.Field()
    source = scrapy.Field()
    pub_time = scrapy.Field()
    pub_org = scrapy.Field()
    implement_date = scrapy.Field()
    pub_wordsize = scrapy.Field()
    keyword = scrapy.Field()
    intro = scrapy.Field()
    potency_level = scrapy.Field()
    timeliness = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
