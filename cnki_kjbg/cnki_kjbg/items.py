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


class cnkiKjbgItem(scrapy.Item):
    title = scrapy.Field()
    article_link = scrapy.Field()
    ask_num = scrapy.Field()
    author = scrapy.Field()
    pub_year = scrapy.Field()
    org_name = scrapy.Field()
    keyword = scrapy.Field()
    type = scrapy.Field()
    page_num = scrapy.Field()
    pub_address = scrapy.Field()
    org_cooperation = scrapy.Field()
    pub_num = scrapy.Field()
    intro = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
