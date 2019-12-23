# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy

class gjypItem(scrapy.Field):
    approval_number=scrapy.Field()
    name=scrapy.Field()
    en_name =  scrapy.Field()
    goods_name = scrapy.Field()
    jixing = scrapy.Field()
    specifications =scrapy.Field()
    permit_holder =scrapy.Field()
    manufacturer =scrapy.Field()
    production_address =scrapy.Field()
    category =scrapy.Field()
    approval_date =scrapy.Field()
    old_approval_number =scrapy.Field()
    drug_standard_code =scrapy.Field()
    drug_standard_code_remark =scrapy.Field()
    databas_query =scrapy.Field()
    remark =scrapy.Field()
    website =scrapy.Field()
    link=scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()