import scrapy
import logging
import re

def get_attachments(response):
    valid_extensions = (".doc", ".docx", ".xlsx", ".xls", ".pdf", ".zip", "wps", ".rar")
    # 取所有超链接
    hrefs = response.css("a::attr(href)").extract()
    texts = response.css('a::text').extract()
    appendix=""
    appendix_name=""
    for i in hrefs :
        if i.endswith(valid_extensions):
            appendix=appendix +response.urljoin(i) +","
    for n in texts:
        if n.endswith(valid_extensions):
                    appendix_name = appendix_name + n +","
    return appendix, appendix_name

#时间格式化
def get_times(srcTime):
    result = srcTime
    if isinstance(srcTime, str):
        list = re.findall(r'([1-9]\d*?\d*)', srcTime)
        if len(list) == 1 and len(list[0]) == 8:  # eg:20190810
            result = list[0][:4] + '-' + list[0][4:6] + '-' + list[0][6:]
        elif len(list) > 2:
            result = list[0] + '-' + list[1].zfill(2) + '-' + list[2].zfill(2)
        else:
            if srcTime != '':
                logging.error('时间格式化异常：' + srcTime)
    return result