import scrapy
import logging

from scrapy_splash import SplashRequest
import requests


def get_attachments(response):
    valid_extensions = [".doc", ".docx", ".xlsx", ".xls", ".pdf", ".zip", "wps", ".rar"]
    # 取所有超链接
    hrefs = response.css("a::attr(href)").extract()
    texts = response.css('a::text').extract()
    result = []
    for i in range(len(hrefs)):
        # 取超链接文本
        href = hrefs[i]
        text = texts[i]
        for ext in valid_extensions:
            if href.endswith(ext):
                file=requests.get(href)
                result.append({
                    "title": text,
                    "file": file
                })
    return result

