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


class bzk_gnbzItem(scrapy.Item):
    name = scrapy.Field()
    code = scrapy.Field()
    status = scrapy.Field()
    xiazai = scrapy.Field()
    committees = scrapy.Field()
    approvalDate = scrapy.Field()
    implementationDate = scrapy.Field()
    sourceWebsite = scrapy.Field()
    ics = scrapy.Field()
    ccs = scrapy.Field()
    en_name = scrapy.Field()
    type = scrapy.Field()
    replace = scrapy.Field()
    caibiao = scrapy.Field()
    caibiao_name = scrapy.Field()
    caibiao_level = scrapy.Field()
    caibiao_type = scrapy.Field()
    dept_host = scrapy.Field()
    dept_pub = scrapy.Field()
    publish_no = scrapy.Field()
    remark = scrapy.Field()
    link = scrapy.Field()
    appendix_name = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
