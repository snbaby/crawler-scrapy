import requests
import logging

class ProxyMiddleWare(object):
    """docstring for ProxyMiddleWare"""

    def process_request(self, request, spider):
        '''对request对象加上proxy'''
        proxy = self.get_random_proxy()
        logging.info("this is request ip:" + proxy)
        try:
            request.meta['splash']['args']['proxy'] = 'https://' + proxy
            logging.info('this is splashrequest!!!')
        except:
            request.meta['proxy'] = 'http://' + proxy

    def process_response(self, request, response, spider):
        '''对返回的response处理'''
        # 如果返回的response状态不是200，重新生成当前request对象
        if response.status != 200:
            proxy = self.get_random_proxy()
            logging.info("this is response ip:" + proxy)
            # 对当前reque加上代理
            request.meta['proxy'] = proxy
            return request
        return response

    def get_random_proxy(self):
        # logging.info('proxy IP:' + requests.get('http://10.8.32.123:5010/get').text)
        # return  requests.get('http://10.8.32.123:5010/get').text
        return  requests.get('http://127.0.0.1:5010/get/').text