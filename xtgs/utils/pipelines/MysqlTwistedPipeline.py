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
                insert into `topic_info_tourongziguanxi_xt_xtgs`(
                `name`,
                `issure`,
                `issue_date`,
                `pro_address`,
                `pre_scale`,
                `real_scale`,
                `deadline_type`,
                `pro_deadline`,
                `tj_start_time`,
                `tj_end_time`,
                `establish_date`,
                `deadline_date`,
                `invest_still`,
                `income_deadline`,
                `pro_state`,
                `pro_type`,
                `invest_method`,
                `money_invest`,
                `money_use`,
                `pre_year_income`,
                `real_year_income`,
                `income_type`,
                `income_explane`,
                `pay_method`,
                `finance_peo`,
                `risk_method`,
                `payment`,
                `pro_highlight`,
                `pro_plan`,
                `raise_account`,
                `money_host_bank`,
                `asset_manager`,
                `host_people`,
                `website`,
                `link`,
                `create_time`,
                `spider_name`,
                `module_name`
                )
                values (%s,%s, %s, %s, %s, %s,%s, %s, %s,%s,%s, %s, %s, %s, %s,%s, %s, %s, %s,%s,%s, %s, %s, %s, %s,%s, %s, %s, %s,%s,%s, %s, %s, %s, %s,%s, %s, %s)
        '''
            parm = (
                item['name'],
                item['issure'],
                item['issue_date'],
                item['pro_address'],
                item['pre_scale'],
                item['real_scale'],
                item['deadline_type'],
                item['pro_deadline'],
                item['tj_start_time'],
                item['tj_end_time'],
                item['establish_date'],
                item['deadline_date'],
                item['invest_still'],
                item['income_deadline'],
                item['pro_state'],
                item['pro_type'],
                item['invest_method'],
                item['money_invest'],
                item['money_use'],
                item['pre_year_income'],
                item['real_year_income'],
                item['income_type'],
                item['income_explane'],
                item['pay_method'],
                item['finance_peo'],
                item['risk_method'],
                item['payment'],
                item['pro_highlight'],
                item['pro_plan'],
                item['raise_account'],
                item['money_host_bank'],
                item['asset_manager'],
                item['host_people'],
                item['website'],
                item['link'],
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
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
