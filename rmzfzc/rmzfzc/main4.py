import sys,os
from scrapy.cmdline import execute

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.system("scrapy crawl hebei_zcjd")
os.system("scrapy crawl hebei_zfwj")
os.system("scrapy crawl heilongjiang_zfwj")
os.system("scrapy crawl heilongjiang")
os.system("scrapy crawl gansu")
os.system("scrapy crawl chongqing")
os.system("scrapy crawl neimenggu_zcjd")
os.system("scrapy crawl shanghai_szfgz")
os.system("scrapy crawl shanghai_szfwj")
os.system("scrapy crawl anhui")
os.system("scrapy crawl chongqing_zcjd")
os.system("scrapy crawl fujian")
os.system("scrapy crawl fujian_zwgkzxd")
