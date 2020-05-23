#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-23 21:56:42
# author calllivecn <c-all@qq.com>


import ssl

from urllib import request


# 这是新方式， 在 3.6 以后
ctx = ssl.SSLContext()
result = request.urlopen("https://localhost:6789", context=ctx)

#result = request.urlopen("https://localhost:6789")

# 这玩意儿，没有～！～！～！。。。 这是旧方式，在3.6 以前
#req = request.Request("https://localhost:6789", unverifiable=False)
#result = request.urlopen(req)

print(result.read().decode())
