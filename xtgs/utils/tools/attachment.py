import scrapy
import logging


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

