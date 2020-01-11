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


class cnki_bzkItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    name = scrapy.Field()
    date = scrapy.Field()
    sub_title = scrapy.Field()
    intro = scrapy.Field()
    version = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
