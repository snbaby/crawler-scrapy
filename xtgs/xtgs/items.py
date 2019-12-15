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


class xtgsItem(scrapy.Item):
    name = scrapy.Field()
    simple_name = scrapy.Field()
    en_name = scrapy.Field()
    create_date = scrapy.Field()
    address = scrapy.Field()
    registe_money = scrapy.Field()
    is_ipo = scrapy.Field()
    company_type = scrapy.Field()
    regist_address = scrapy.Field()
    partner_compose = scrapy.Field()
    partner_bg = scrapy.Field()
    company_intro = scrapy.Field()
    legal_person = scrapy.Field()
    dongshizhang = scrapy.Field()
    shareholder = scrapy.Field()
    general_manager = scrapy.Field()
    aum = scrapy.Field()
    avg_yield = scrapy.Field()
    pro_hold_rate = scrapy.Field()
    company_website = scrapy.Field()
    telephone = scrapy.Field()
    fax = scrapy.Field()
    postcode = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
