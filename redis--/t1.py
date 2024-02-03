#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-03 12:33:42
# author calllivecn <c-all@qq.com>

import redis


# 连接到 localhost 的 6379 端口
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 存储和获取简单字符串
r.setnx('foo', 'bar')  # 返回 True
r.incr("foo")
print(f"{r.get('foo')=}")  # 输出 'bar'


r.set("zx", 5, ex=50)

print(f'{r.ttl("zx")=}')

print(r.scan(0))

