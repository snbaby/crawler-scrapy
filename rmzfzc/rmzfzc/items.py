# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
from urllib import parse
from scrapy.item import Field
import scrapy
from scrapy.loader.processors import TakeFirst, MapCompose,Join



class rmzfzcItem(scrapy.Item):
    title = scrapy.Field()
    article_num = scrapy.Field()
    content = scrapy.Field()
    appendix = scrapy.Field()
    source = scrapy.Field()
    time = scrapy.Field()
    province = scrapy.Field()
    city = scrapy.Field()
    area = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
