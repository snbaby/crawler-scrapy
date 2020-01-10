import sys,os
from scrapy.cmdline import execute

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
os.system("scrapy crawl guangdong")
os.system("scrapy crawl guangxi")
os.system("scrapy crawl hainan")
os.system("scrapy crawl guizhou")
os.system("scrapy crawl gansu")
os.system("scrapy crawl xinjiang")
