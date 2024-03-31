#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-04 15:46:01
# author calllivecn <calllivecn@outlook.com>

import sys
import time
#import ssl
import json
import socket
from urllib import parse, request




def useproxy(url):

    parse_url = parse.urlparse(url)

    headers = {
            "Host": parse_url.netloc,
            "User-Agent": "curl/7.68.0",
            #"Accept-Charset": "UTF-8",
            "Accept-Encoding": "identity",
            #"Proxy-Connection": "Keep-Alive",
            }

    req = request.Request(url, headers=headers)


    proxy_handler = request.ProxyHandler({"http": "127.0.0.1:8080", "https": "10.1.2.1:9998"})

    print("req.headers -->\n", req.headers)
    opener = request.build_opener(proxy_handler)

    html_bytes = opener.open(req).read()
    #.decode("utf-8")
    return html_bytes



#useproxy("http://www.baidu.com")
result = useproxy(sys.argv[1])

print("recv data content: ", result.decode("utf-8"))
print("recv data length: ", len(result))
