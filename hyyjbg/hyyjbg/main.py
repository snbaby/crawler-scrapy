# -*- coding: utf-8 -*-import sys,osfrom scrapy.cmdline import executesys.path.append(os.path.abspath(os.path.dirname(__file__)))sys.path.append(os.path.abspath(os.path.dirname(__file__)+"/../"))os.system("scrapy crawl dfcfw")os.system("scrapy crawl hxt")os.system("scrapy crawl jrj")os.system("scrapy crawl shxt")os.system("scrapy crawl ths")os.system("scrapy crawl wqj")os.system("scrapy crawl xt")os.system("scrapy crawl yyxty")os.system("scrapy crawl zgxtdj")os.system("scrapy crawl zgxt")