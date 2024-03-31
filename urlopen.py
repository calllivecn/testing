#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-24 13:58:37
# author calllivecn <calllivecn@outlook.com>


import sys

from urllib.request import urlopen, Request
from functools import partial

block = 1<<14 # 16k

headers = {"User-Agent": "author: calllivecn, url: https://github.com/calllivecn/"}

req = Request(sys.argv[1], headers=headers)

response = urlopen(req, timeout=3)

c = 0 

for data in iter(partial(response.read, block), b""):
    l = len(data)
    c+=1
    print(c , "kB", l, "b")

response.close()


