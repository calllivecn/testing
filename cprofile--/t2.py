#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-04 00:42:47
# author calllivecn <c-all@qq.com>

# 推荐写法。代码耗时：20.6秒
import math

def main():  # 定义到函数中，以减少全部变量使用
    size = 10000
    for x in range(size):
        for y in range(size):
            z = math.sqrt(x) + math.sqrt(y)

main()


