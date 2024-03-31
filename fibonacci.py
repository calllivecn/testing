#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-07 05:12:20
# author calllivecn <calllivecn@outlook.com>

import sys


try:
    n = int(sys.argv[1]) + 1
except (IndexError, ValueError):
    n = 50 + 1

def fib(n):
    a, b = 0, 1
    for i in range(n):
        print("{} : {}".format(i,b))
        a,b = b,a+b

    return a


print("N:", fib(n))
