# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy

class schoolEssentialLibraryItem(scrapy.Field):
    name = scrapy.Field()
    type = scrapy.Field()
    province =  scrapy.Field()
    city = scrapy.Field()
    education = scrapy.Field()
    email =scrapy.Field()
    phone =scrapy.Field()
    website =scrapy.Field()
    survey =scrapy.Field()
    major =scrapy.Field()
    sourceWebsite =scrapy.Field()
    link =scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class specialtiesInSchoolsItem(scrapy.Field):
    school_name=scrapy.Field()
    major=scrapy.Field()
    website =  scrapy.Field()
    link =scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class recruitPlanLibraryItem(scrapy.Field):
    name=scrapy.Field()
    major=scrapy.Field()
    secondLevel =  scrapy.Field()
    subject =scrapy.Field()
    local = scrapy.Field()
    majorType = scrapy.Field()
    particularYear = scrapy.Field()
    batch = scrapy.Field()
    planRecruit = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()


class schoolEmploymentLibraryItem(scrapy.Field):
    name=scrapy.Field()
    maleRatio=scrapy.Field()
    womanRatio =  scrapy.Field()
    RateOfEmployment =scrapy.Field()
    entrance = scrapy.Field()
    goingAbroad = scrapy.Field()
    create_time = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class employmentLocalLibraryItem(scrapy.Field):
    name = scrapy.Field()
    local = scrapy.Field()
    proportion = scrapy.Field()
    create_time = scrapy.Field()
    website = scrapy.Field()
    link = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class majorInfoLibraryItem(scrapy.Field):
    majorName = scrapy.Field()
    majorCode = scrapy.Field()
    majorPopularity = scrapy.Field()
    AcademicDegree = scrapy.Field()
    studyYear = scrapy.Field()
    subjectType = scrapy.Field()
    majorType = scrapy.Field()
    arrangement = scrapy.Field()
    maleRatio = scrapy.Field()
    womanRatio = scrapy.Field()
    detail = scrapy.Field()
    FirstImpression = scrapy.Field()
    sourceWebsite = scrapy.Field()
    link = scrapy.Field()
    create_time = scrapy.Field()
    txt = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class majorLocalLibraryItem(scrapy.Field):
    majorName = scrapy.Field()
    majorCode = scrapy.Field()
    local = scrapy.Field()
    proportion = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class majorObtainLibraryItem(scrapy.Field):
    majorName = scrapy.Field()
    majorCode = scrapy.Field()
    particularYear = scrapy.Field()
    rateOfEmployment = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()

class schoolInMajorItem(scrapy.Field):
    major_name = scrapy.Field()
    colleges_name = scrapy.Field()
    create_time = scrapy.Field()
    spider_name = scrapy.Field()
    module_name = scrapy.Field()