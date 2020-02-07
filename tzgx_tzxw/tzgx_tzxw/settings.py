# -*- coding: utf-8 -*-

# Scrapy settings for haiguanshuju project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'tzgx_tzxw'

SPIDER_MODULES = ['tzgx_tzxw.spiders']
NEWSPIDER_MODULE = 'tzgx_tzxw.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'haiguanshuju (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language':'zh-CN,zh;q=0.9,zh-TW;q=0.8,ko;q=0.7,en;q=0.6',
#   'Accept-Encoding':'gzip, deflate',
#   # 'Host': 'www.customs.gov.cn',
#   # 'Cookie':'BIGipServerpool_sy_www.customs.gov.cn_80=2855305162.20480.0000; gwdshare_firstime=1562122232530; _gscu_1524496263=62122232cwvgfv12; _gscbrs_1524496263=1; ADMINCONSOLESESSION=mjsJ8YoIqe9R4QuGDBQe-GMg4KRurRjy5ByU4OArcBFoNemjCsPe!1691983987; DAMDDOS=2855305162.20480.0000; EPORTALAPPJSESSIONID=3Vkc3-h0stan-5Wx7lhii8aUWxfCX7XRyjBLiHi2W8cRIGoMr1Yc!1691983987; EPORTALJSESSIONID=4GAfmB71IxXfodMe6p8-D2w8juYFFxwZMELttVirEwr8QZAj2R50!1691983987; EPORTALAPPLYJSESSIONID=KlwfmB72pyRglroAORlgow09XbF6Mp93mv6ClALqWuiz6XArtzSx!1691983987; TSPD_101=087968f3e8ab280076fd12943efe9a1ed0ac05179f367ecb2e63584b643c86978b7e2e4a2377ea3196c6c4442d38b7d608c66b8258051000cfbe254dd4dadced504801a344ebc9d0:; TS01d6ec82=01ef8f99f1b00ef36ea3467434989a22b68cdadc8252223cf22a1c20f070f393864afedd95eccd49ccef56fec0fcc858fb1aa16572'
# }
# COOKIES_ENABLED = False
# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'haiguanshuju.middlewares.HaiguanshujuSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#     # 'hgsj.middlewares.ProxyMiddleware': 128,
#     'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
#     'hgsj.middlewares.MyUserAgentMiddleware': 544,
# }

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'haiguanshuju.pipelines.TJkxPipeline': 300,
#     'hgsj.pipelines.MysqlTwistedPipeline': 128,
#     'hgsj.pipelines.DuplicatesPipeline': 64,
}
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

#LOG_ENABLED = True
#LOG_FILE = "spiders.log"
LOG_LEVEL = "DEBUG"

MYSQL_HOST = '10.8.32.125'
# MYSQL_HOST = 'rm-8vbif49m6k7l651e5fo.mysql.zhangbei.rds.aliyuncs.com'
# MYSQL_HOST = '192.168.43.201'
MYSQL_USER = 'root'
#MYSQL_PASSWORD = 'Liqin1988'
MYSQL_PASSWORD ='Admin123!'

MYSQL_DB = 'engineering-brain'
MYSQL_PORT = 3306
MYSQL_CHRSET = 'utf8'

SPLASH_URL = "http://47.106.239.73:8050/"

# REDIS_HOST = '10.8.32.123'
# REDIS_HOST = '127.0.0.1'
# REDIS_HOST = '47.105.111.235'
# REDIS_PORT = 6379


# # scrapy-redis 配置
# # 调度器
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# # 去重类
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# # 断点续爬
# SCHEDULER_PERSIST = True
#
# # 指定排序爬取地址时使用的队列，
# # 默认的 按优先级排序(Scrapy默认)，由sorted set实现的一种非FIFO、LIFO方式。
# SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'
# # 可选的 按先进先出排序（FIFO）
# SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderQueue'
# 可选的 按后进先出排序（LIFO）
# SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderStack'
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408]
