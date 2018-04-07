#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-07 05:12:20
# author calllivecn <c-all@qq.com>



a, b = 0, 1

for i in range(1,51):
    print("{} : {}".format(i,b))
    a,b = b,a+b
