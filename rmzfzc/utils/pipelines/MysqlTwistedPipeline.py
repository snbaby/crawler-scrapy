import copy
import datetime
import pymysql
from twisted.enterprise import adbapi
from scrapy.exceptions import DropItem

class MysqlTwistedPipeline(object):

    def __init__(self, dbpool):
        self.dbpool = dbpool
        self.fp = open('msyql_save_err.log', 'a', encoding='utf-8')

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

    def process_item(self, item, spider):
        try:
            # 使用twisted将mysql插入变成异步执行
            asynItem = copy.deepcopy(item)
            query = self.dbpool.runInteraction(self.do_insert, asynItem)
            query.addErrback(self.handle_error, item, spider)  # 处理异常
        except Exception as e:
            self.fp.write(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') + '----' + e.__str__() + '\n')
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        self.fp.write(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') + '----' + str(failure) + '\n')

    def do_insert(self, cursor, item):
        try:
            sql = f'''
                insert into `topic_info_government_policy`(
                `title`,
                `article_num`,
                `content`,
                `appendix`,
                `source`,
                `time`,
                `province`,
                `city`,
                `area`,
                `website`,
                `link`,
                )
                values (%s,%s, %s, 
                %s, %s, %s,%s)
        '''
            parm = (
                item['title'],
                item['article_num'],
                item['content'],
                item['appendix'],
                item['source'],
                item['time'],
                item['province'],
                item['city'],
                item['area'],
                item['website'],
                item['link'],
            )
            cursor.execute(sql, parm)
        except Exception as e:
            raise DropItem("Duplicate item found: %s" % item)
            self.fp.write(datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') + '----' + e.__str__() + '\n')

        def close_spider(self, spider):
            self.dbpool.close()
            self.fp.close()