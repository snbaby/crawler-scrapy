# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy

class yyqxItem(scrapy.Item):
    registration_code = scrapy.Field()
    registrar = scrapy.Field()
    registrar_address = scrapy.Field()
    production_address = scrapy.Field()
    agent_name = scrapy.Field()
    agent_address = scrapy.Field()
    name = scrapy.Field()
    specifications = scrapy.Field()
    compose = scrapy.Field()
    scope = scrapy.Field()
    other = scrapy.Field()
    remark = scrapy.Field()
    approval_date = scrapy.Field()
    period_of_validity = scrapy.Field()
    appendix = scrapy.Field()
    product_standard = scrapy.Field()
    category = scrapy.Field()
    change_date = scrapy.Field()
    zip_code = scrapy.Field()
    major_component = scrapy.Field()
    usage = scrapy.Field()
    storage_conditions = scrapy.Field()
    approval_dept = scrapy.Field()
    modify = scrapy.Field()
    notes = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()