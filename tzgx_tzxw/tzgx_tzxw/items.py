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


class tzgx_tzxwItem(scrapy.Item):
    job = scrapy.Field()
    company_name = scrapy.Field()
    industry = scrapy.Field()
    location = scrapy.Field()
    salary = scrapy.Field()
    time = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    type = scrapy.Field()
    source = scrapy.Field()
    content = scrapy.Field()
    education = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
