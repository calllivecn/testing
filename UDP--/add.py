#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-14 10:42:33
# author calllivecn <c-all@qq.com>

import time

import numba

def f1(n):
    i=0.1
    for _ in range(n):
        i+=0.2
    print("result: %f", i)

@numba.jit
def f2(n):
    i=0.1
    for _ in range(n):
        i+=0.2
    print("result: %f", i)

count = 1000000000

t1 = time.time()
f1(count)
t2 = time.time()
print("耗时：", t2 -t1, "/秒")


t1 = time.time()
f2(count)
t2 = time.time()
print("耗时：", t2 -t1, "/秒")

