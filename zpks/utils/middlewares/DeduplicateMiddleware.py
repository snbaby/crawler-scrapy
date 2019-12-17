import redis
from utils.pipelines.BloomFilter import PyBloomFilter
from scrapy.exceptions import IgnoreRequest

class DeduplicateMiddleware(object):
    # 设置redis连接
    def __init__(self):
        return
        host = '47.106.239.73'
        port = 6379
        pool = redis.ConnectionPool(host=host, port=port, db=1)
        conn = redis.StrictRedis(connection_pool=pool)
        self.bf = PyBloomFilter(conn=conn)

    def process_request(self, request, spider):
        return None
        # 检查request是否已经请求过，如果请求过，则IgnoreRequest放弃连接
        bf2 = self.bf.is_exist(request.url)
        if bf2:
            raise IgnoreRequest("Duplicate item found:%s" % request.url)
        return None