#!/usr/bin/env python3
#coding=utf-8
# date 2018-06-13 08:31:50
# author calllivecn <calllivecn@outlook.com>


import sys

stdin =  sys.stdin.buffer
stdout = sys.stdout.buffer
data = True
while data:
    data = stdin.read(1024)
    stdout.write(data)
    print(len(data))


