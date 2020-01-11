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


class hylwItem(scrapy.Item):
    title = scrapy.Field()
    author = scrapy.Field()
    organization = scrapy.Field()
    name = scrapy.Field()
    time = scrapy.Field()
    intro = scrapy.Field()
    address = scrapy.Field()
    type = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
