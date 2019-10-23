#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-24 13:58:37
# author calllivecn <c-all@qq.com>


import sys

from urllib.request import urlopen
from functools import partial

block = 1<<14 # 16k

response = urlopen(sys.argv[1], timeout=3)

c = 1 

for data in iter(partial(response.read, block), b""):
    print(c , "kB", len(data))
    c+=1

response.close()


