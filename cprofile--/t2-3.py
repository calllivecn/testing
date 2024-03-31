#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-04 00:47:24
# author calllivecn <calllivecn@outlook.com>

# 推荐写法。代码耗时：7.9秒
import math

def computeSqrt(size: int):
    result = []
    append = result.append
    sqrt = math.sqrt    # 赋值给局部变量
    for i in range(size):
        append(sqrt(i))  # 避免 result.append 和 math.sqrt 的使用
    return result

def main():
    size = 10000
    for _ in range(size):
        result = computeSqrt(size)

main()

