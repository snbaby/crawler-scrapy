import scrapy
import logging
import re

def get_attachments(response):
    valid_extensions = [".doc", ".docx", ".xlsx", ".xls", ".pdf", ".zip", "wps", ".rar"]
    # 取所有超链接
    hrefs = response.css("a::attr(href)").extract()
    texts = response.css('a::text').extract()
    logging.info(hrefs, texts)
    appendix=""
    appendix_name=""
    for i in range(len(hrefs)):
        # 取超链接文本
        href = hrefs[i]
        text=""
        for ext in valid_extensions:
            if href.endswith(ext):
                appendix=appendix + href +";"
                if i >= 0 and i < len(texts):
                    text=texts[i]
                appendix_name=appendix_name + text +";"
    return appendix, appendix_name

#时间格式化
def get_times(srcTime):
    list = re.findall(r'([1-9]\d*?\d*)', srcTime)
    result = ''
    if len(list) == 1 and len(list[0]) == 8:  # eg:20190810
        result = list[0][:4] + '-' + list[0][4:6] + '-' + list[0][6:]
    elif len(list) > 2:
        result = list[0] + '-' + list[1].zfill(2) + '-' + list[2].zfill(2)
    else:
        if srcTime != '':
            logging.error('时间格式化异常：' + srcTime)
        result = srcTime
    return result