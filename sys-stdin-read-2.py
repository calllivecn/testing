#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-25 16:13:49
# https://github.com/calllivecn


import io
import sys



fp_rb = io.open(sys.stdin.fileno(),mode="rb")

if fp_rb.isatty():
    print("fp is tty")
else:
    print("fp is not tty")

print("tell() --> ", fp_rb.tell())

data = True
while data:
    data = fp_rb.read(8)
    #print(len(data),end='，')

print("done")
