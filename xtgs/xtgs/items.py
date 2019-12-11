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
    issure = scrapy.Field()
    issue_date = scrapy.Field()
    pro_address = scrapy.Field()
    pre_scale = scrapy.Field()
    real_scale = scrapy.Field()
    deadline_type = scrapy.Field()
    pro_deadline = scrapy.Field()
    tj_start_time = scrapy.Field()
    tj_end_time = scrapy.Field()
    establish_date = scrapy.Field()
    deadline_date = scrapy.Field()
    invest_still = scrapy.Field()
    income_deadline = scrapy.Field()
    pro_state = scrapy.Field()
    pro_type = scrapy.Field()
    invest_method = scrapy.Field()
    money_invest = scrapy.Field()
    money_use = scrapy.Field()
    pre_year_income = scrapy.Field()
    real_year_income = scrapy.Field()
    income_type = scrapy.Field()
    income_explane = scrapy.Field()
    pay_method = scrapy.Field()
    finance_peo = scrapy.Field()
    risk_method = scrapy.Field()
    payment = scrapy.Field()
    pro_highlight = scrapy.Field()
    pro_plan = scrapy.Field()
    raise_account = scrapy.Field()
    money_host_bank = scrapy.Field()
    asset_manager = scrapy.Field()
    host_people = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()
