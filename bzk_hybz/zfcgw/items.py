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


class ztbkItem(scrapy.Item):
    title = scrapy.Field()
    content = scrapy.Field()
    appendix = scrapy.Field()
    category = scrapy.Field()
    time = scrapy.Field()
    source = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    type = scrapy.Field()
    region = scrapy.Field()
    appendix_name = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
    txt = scrapy.Field()
