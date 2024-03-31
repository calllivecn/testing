#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-04 00:39:24
# author calllivecn <calllivecn@outlook.com>

# 不推荐写法。代码耗时：26.8秒
import math

size = 10000
for x in range(size):
    for y in range(size):
        z = math.sqrt(x) + math.sqrt(y)

