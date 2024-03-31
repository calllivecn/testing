#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-04 00:45:43
# author calllivecn <calllivecn@outlook.com>


# 第二次优化写法。代码耗时：9.9秒
import math

def computeSqrt(size: int):
    result = []
    sqrt = math.sqrt  # 赋值给局部变量
    for i in range(size):
        result.append(sqrt(i))  # 避免math.sqrt的使用
    return result

def main():
    size = 10000
    for _ in range(size):
        result = computeSqrt(size)

main()

