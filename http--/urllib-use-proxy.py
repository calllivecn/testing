#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-04 15:46:01
# author calllivecn <c-all@qq.com>

#import ssl
import time
import json
import socket
from urllib import parse, request




def useproxy(url):

    parse_url = parse.urlparse(url)


    req = request.Request(url)

    req.add_header("Host", parse_url.netloc)

    proxy_handler = request.ProxyHandler({"http": "localhost:8080", "https": "127.0.0.1:8080"})

    print("req.headers -->\n", req.headers)
    opener = request.build_opener(proxy_handler)

    return opener.open(req).read().decode("utf-8")



#useproxy("http://www.baidu.com")
result = useproxy("https://www.baidu.com")

print("recv data length: ", len(result))
print("recv data content: ", result)