#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-07 05:12:20
# author calllivecn <c-all@qq.com>

import sys

a, b = 0, 1

try:
    n = int(sys.argv[1]) + 1
except (IndexError, ValueError):
    n = 50 + 1

for i in range(1, n):
    print("{} : {}".format(i,b))
    a,b = b,a+b
