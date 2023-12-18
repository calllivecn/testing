#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-04 00:45:14
# author calllivecn <c-all@qq.com>

# 不推荐写法。代码耗时：14.5秒
import math

def computeSqrt(size: int):
    result = []
    for i in range(size):
        result.append(math.sqrt(i))
    return result

def main():
    size = 10000
    for _ in range(size):
        result = computeSqrt(size)

main()
