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


class tzgx_tzgsItem(scrapy.Item):
    name = scrapy.Field()
    simple_name = scrapy.Field()
    en_name = scrapy.Field()
    headquarters = scrapy.Field()
    register_location = scrapy.Field()
    time = scrapy.Field()
    industry = scrapy.Field()
    official_website = scrapy.Field()
    introduction = scrapy.Field()
    phone = scrapy.Field()
    fax = scrapy.Field()
    location = scrapy.Field()
    zip_code = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    company_info = scrapy.Field()
    content = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
