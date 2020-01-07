import copy
import time
import pymysql
from twisted.enterprise import adbapi
from scrapy.exceptions import DropItem
import logging

class MysqlTwistedPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            port=settings['MYSQL_PORT'],
            db=settings["MYSQL_DB"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset=settings['MYSQL_CHRSET'],
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("pymysql", **dbparms)

        return cls(dbpool)

    def open_spider(self, spider):
        self.spider = spider

    def process_item(self, item, spider):
        try:
            # 使用twisted将mysql插入变成异步执行
            asynItem = copy.deepcopy(item)
            query = self.dbpool.runInteraction(self.do_insert, asynItem)
            query.addErrback(self.handle_error, item, spider)  # 处理异常
        except Exception as e:
            logging.error("Got exception {}, {}".format(e))

        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        logging.error("spider {} on itemm failed: {}".format(self.spider.name, str(failure)))

    def do_insert(self, cursor, item):
        logging.info(self.spider.name + ": " + "insert into mysql........")
        try:
            sql = f'''
                    insert into `country_standard_library`(
                    `name`,
                    `code`,
                    `status`,
                    `xiazai`,
                    `committees`,
                    `approvalDate`,
                    `implementationDate`,
                    `sourceWebsite`,
                    `ics`,
                    `ccs`,
                    `en_name`,
                    `type`,
                    `replace`,
                    `caibiao`,
                    `caibiao_name`,
                    `caibiao_level`,
                    `caibiao_type`,
                    `dept_host`,
                    `dept_pub`,
                    `publish_no`,
                    `remark`,
                    `create_time`,
                    `link`,
                    `appendix_name`,
                    `spider_name`,
                    `module_name`
                    )
                values (%s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s,%s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s,%s,%s)
            '''
            parm = (
                item['name'],
                item['code'],
                item['status'],
                item['xiazai'],
                item['committees'],
                item['approvalDate'],
                item['implementationDate'],
                item['sourceWebsite'],
                item['ics'],
                item['ccs'],
                item['en_name'],
                item['type'],
                item['replace'],
                item['caibiao'],
                item['caibiao_name'],
                item['caibiao_level'],
                item['caibiao_type'],
                item['dept_host'],
                item['dept_pub'],
                item['publish_no'],
                item['remark'],
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                item['link'],
                item['appendix_name'],
                item['spider_name'],
                item['module_name']
            )
            cursor.execute(sql, parm)
            logging.info(self.spider.name + ": " + "insert into mysql success")
        except Exception as e:
            logging.info("Spider insert item failed: {}, {}".format(e, e.args))
            raise DropItem("Duplicate item found: %s" % item)

    def close_spider(self, spider):
        self.dbpool.close()
        self.spider = None
