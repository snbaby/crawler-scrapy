# -*- coding: utf-8 -*-
import sys,os
from scrapy.cmdline import execute

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.system("scrapy crawl jilin_zwgk")
os.system("scrapy crawl quanguo_xxgk")
os.system("scrapy crawl shaanxi")
os.system("scrapy crawl shandong")
os.system("scrapy crawl shanghai_zcjd")
os.system("scrapy crawl sichuan")
os.system("scrapy crawl xinjiang")
os.system("scrapy crawl xizang")
os.system("scrapy crawl yunnan")
os.system("scrapy crawl zhejiang")
os.system("scrapy crawl zhejiang_zfwj")
