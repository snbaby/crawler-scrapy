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
        logging.error(
            "spider {} on itemm failed: {}".format(
                self.spider.name,
                str(failure)))

    def do_insert(self, cursor, item):
        logging.info(self.spider.name + ": " + "insert into mysql........")
        try:
            sql = f'''
                    insert into `international_standard_library`(
                    `name`,
                    `code`,
                    `status`,
                    `committees`,
                    `approvalDate`,
                    `implementationDate`,
                    `sourceWebsite`,
                    `ics`,
                    `pub_lang`,
                    `pub_organization`,
                    `replace`,
                    `replaced`,
                    `dept_host`,
                    `scope`,
                    `create_time`,
                    `link`,
                    `spider_name`,
                    `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s,%s,%s,%s, %s, %s, %s, %s)
                    '''
            parm = (
                item['name'],
                item['code'],
                item['status'],
                item['committees'],
                item['approvalDate'],
                item['implementationDate'],
                item['sourceWebsite'],
                item['ics'],
                item['pub_lang'],
                item['pub_organization'],
                item['replace'],
                item['replaced'],
                item['dept_host'],
                item['scope'],
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                item['link'],
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
