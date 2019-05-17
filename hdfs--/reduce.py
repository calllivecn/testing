#!/usr/bin/env python3
# coding=utf-8
# date 2019-05-15 11:03:38
# author calllivecn <c-all@qq.com>


import sys

result = {}
for line in sys.stdin:
    kvs = line.strip().split(' ')
    k = kvs[0]
    v = kvs[1]
    if k in result:
        result[k]+=1
    else:
        result[k] = 1

for k,v in result.items():
    print("{}\t{}".format(k,v))
