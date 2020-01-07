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


class bzk_gjbzItem(scrapy.Item):
    name = scrapy.Field()
    code = scrapy.Field()
    status = scrapy.Field()
    committees = scrapy.Field()
    approvalDate = scrapy.Field()
    implementationDate = scrapy.Field()
    sourceWebsite = scrapy.Field()
    ics = scrapy.Field()
    pub_lang = scrapy.Field()
    pub_organization = scrapy.Field()
    replace = scrapy.Field()
    replaced = scrapy.Field()
    dept_host = scrapy.Field()
    scope = scrapy.Field()
    create_time = scrapy.Field()
    link = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
