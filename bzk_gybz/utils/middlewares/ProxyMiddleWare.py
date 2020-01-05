import requests

class ProxyMiddleWare(object):
    """docstring for ProxyMiddleWare"""

    def process_request(self, request, spider):
        proxy = self.get_random_proxy()
        '''对request对象加上proxy'''
        print("this is request ip:" +proxy)
        try:
            request.meta['proxy'] = 'http://'+ proxy
        except:
            request.meta['splash']['args']['proxy'] ='http://'+ proxy


    def process_response(self, request, response, spider):
        # 如果返回的response状态不是200，重新生成当前request对象
        if response.status != 200:
            proxy = self.get_random_proxy()
            print("this is respo"
                  "nse ip:" + proxy)
            # 对当前reque加上代理
            request.meta['proxy'] ='http://'+ proxy
            return request
        return response

    def get_random_proxy(self):
        '''随机从IP数据库中读取proxy'''
        return requests.get('http://10.8.32.124:5010/get').content.decode('utf-8')