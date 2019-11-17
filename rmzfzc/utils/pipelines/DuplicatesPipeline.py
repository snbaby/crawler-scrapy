import redis
import logging
from scrapy.exceptions import DropItem
from .BloomFilter import PyBloomFilter

class DuplicatesPipeline(object):

    def __init__(self):
        host = '47.106.239.73'
        port = 6379
        pool = redis.ConnectionPool(host=host, port=port, db=1)
        conn = redis.StrictRedis(connection_pool=pool)
        self.bf =PyBloomFilter(conn=conn)

    def process_item(self, item, spider):
        bf2 = self.bf.is_exist(item['link'])
        if bf2 :
            raise DropItem("Duplicate item found:%s" % item)
        self.bf.add(item['link'])
        logging.info("=====================================================item inserted, added!")
        return item