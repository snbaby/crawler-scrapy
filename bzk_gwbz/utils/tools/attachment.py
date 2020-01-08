import scrapy
import logging
import re

def get_attachments(response):
    valid_extensions = [".doc", ".docx", ".xlsx", ".xls", ".pdf", ".zip", ".wps", ".rar"]
    # 取所有超链接
    list = response.xpath("//a")
    appendix=""
    appendix_name=""
    for a in list:
        # 取超链接文本
        href = a.xpath('./@href').extract_first()
        name = a.xpath('./text()').extract_first()
        if href and name:
            for ext in valid_extensions:
                if href.endswith(ext) or name.endswith(ext):
                    appendix = appendix + response.urljoin(href) + ","
                    appendix_name = appendix_name + name + ","
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