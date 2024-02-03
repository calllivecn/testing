#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-03 14:26:07
# author calllivecn <c-all@qq.com>


import redis


# 连接到 localhost 的 6379 端口
r = redis.Redis(host='localhost', port=6379, decode_responses=True)



def producer(count=100):
    for i in range(count):
        r.xadd("stream1", 









