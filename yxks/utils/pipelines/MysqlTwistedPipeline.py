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
            if item['insert_tpye'] == 'school':
                sql = f'''
                    insert into `school_essential_library`(
                        `name`,
                        `type`,
                        `province`,
                        `city`,
                        `education`,
                        `email`,
                        `phone`,
                        `website`,
                        `survey`,
                        `major`,
                        `sourceWebsite`,
                        `link`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s,%s, %s, %s,%s,%s, %s, %s, %s, %s)
                '''
                parm = (
                    item['name'],
                    item['type'],
                    item['province'],
                    item['city'],
                    item['education'],
                    item['email'],
                    item['phone'],
                    item['website'],
                    item['survey'],
                    item['major'],
                    item['sourceWebsite'],
                    item['link'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'zhuanye':
                sql = f'''
                    insert into `specialties_in_schools`(
                        `school_name`,
                        `major`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s)
                '''
                parm = (
                    item['school_name'],
                    item['major'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'zhaosheng':
                sql = f'''
                    insert into `recruit_plan_library`(
                        `name`,
                        `major`,
                        `secondLevel`,
                        `subject`,
                        `local`,
                        `majorType`,
                        `particularYear`,
                        `batch`,
                        `planRecruit`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s,%s,%s,%s, %s, %s, %s)
                '''
                parm = (
                    item['name'],
                    item['major'],
                    item['secondLevel'],
                    item['subject'],
                    item['local'],
                    item['majorType'],
                    item['particularYear'],
                    item['batch'],
                    item['planRecruit'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'employment':
                sql = f'''
                    insert into `school_employment_library`(
                        `name`,
                        `maleRatio`,
                        `womanRatio`,
                        `RateOfEmployment`,
                        `entrance`,
                        `goingAbroad`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s,%s,%s,%s)
                '''
                parm = (
                    item['name'],
                    item['maleRatio'],
                    item['womanRatio'],
                    item['RateOfEmployment'],
                    item['entrance'],
                    item['goingAbroad'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'employment_local':
                sql = f'''
                    insert into `employment_local_library`(
                        `name`,
                        `local`,
                        `proportion`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s)
                '''
                parm = (
                    item['name'],
                    item['local'],
                    item['proportion'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'major_info_library':
                sql = f'''
                    insert into `major_info_library`(
                        `majorName`,
                        `majorCode`,
                        `majorPopularity`,
                        `AcademicDegree`,
                        `studyYear`,
                        `subjectType`,
                        `majorType`,
                        `arrangement`,
                        `maleRatio`,
                        `womanRatio`,
                        `detail`,
                        `FirstImpression`,
                        `sourceWebsite`,
                        `link`,
                        `create_time`,
                        `txt`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)
                '''
                parm = (
                    item['majorName'],
                    item['majorCode'],
                    item['majorPopularity'],
                    item['AcademicDegree'],
                    item['studyYear'],
                    item['subjectType'],
                    item['majorType'],
                    item['arrangement'],
                    item['maleRatio'],
                    item['womanRatio'],
                    item['detail'],
                    item['FirstImpression'],
                    item['sourceWebsite'],
                    item['link'],
                    item['txt'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'major_local_library':
                sql = f'''
                    insert into `major_local_library`(
                        `majorName`,
                        `majorCode`,
                        `local`,
                        `proportion`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s, %s)
                '''
                parm = (
                    item['majorName'],
                    item['majorCode'],
                    item['local'],
                    item['proportion'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'major_obtain_library':
                sql = f'''
                    insert into `major_obtain_library`(
                        `majorName`,
                        `majorCode`,
                        `particularYear`,
                        `rateOfEmployment`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s, %s, %s)
                '''
                parm = (
                    item['majorName'],
                    item['majorCode'],
                    item['particularYear'],
                    item['rateOfEmployment'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
            elif item['insert_tpye'] == 'school_in_major':
                sql = f'''
                    insert into `school_in_major`(
                        `major_name`,
                        `colleges_name`,
                        `create_time`,
                        `spider_name`,
                        `module_name`
                    )
                    values (%s,%s, %s, %s, %s)
                '''
                parm = (
                    item['major_name'],
                    item['colleges_name'],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    item['spider_name'],
                    item['module_name']
                )
                cursor.execute(sql, parm)
                logging.info(self.spider.name + ": " + "insert into mysql success")
        except Exception as e:
            logging.error("Spider insert item failed: {}, {}".format(e, e.args))
            raise DropItem("Duplicate item found: %s" % item)

    def close_spider(self, spider):
        self.dbpool.close()
        self.spider = None
