#!/usr/bin/env python3
#coding=utf-8
# date 2018-06-13 08:31:50
# author calllivecn <c-all@qq.com>


import sys,os

stdin =  sys.stdin.fileno()
data = True
while data:
    data = os.read(stdin,1024)
    print(len(data),data)
