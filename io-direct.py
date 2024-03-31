#!/usr/bin/env python3
# coding=utf-8
# date 2019-06-05 15:50:59
# author calllivecn <calllivecn@outlook.com>

import os
import sys
import mmap


BLOCK = 1<<20

def memory_alignment(buf):
    m = mmap.mmap(-1, buf)
    s = bytes(buf)
    m.write(s)
    return m


BUF = mem(BLOCK)

filename = sys.argv[1]

filesize = os.path.getsize(filename)


fp = os.open(filename, os.O_RDWR | os.O_DIRECT)

count, c = divmod(filesize, BLOCK)

if c > 0 :
    count += 1

for _ in range(count):
    os.write(fp, BUF)

os.close(fp)


