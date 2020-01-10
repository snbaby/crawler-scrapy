import sys,os
from scrapy.cmdline import execute

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.system("scrapy crawl neimenggu_zcjd")
os.system("scrapy crawl jiangsu")
os.system("scrapy crawl anhui")
os.system("scrapy crawl fujian")
os.system("scrapy crawl fujian_zwgkzxd")
os.system("scrapy crawl hubei")
os.system("scrapy crawl hunan")
