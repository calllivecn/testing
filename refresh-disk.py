#!/usr/bin/env python3
# coding=utf-8
# date 2022-02-10 20:56:07
# author calllivecn <c-all@qq.com>


import io
import sys
import pathlib

BUF=1<<20


filename = pathlib.Path(sys.argv[1])
filesize = filename.stat().st_size

# 每100M 输出进度
c = 100

cur_size = 0

with open(filename, "r+b") as f:
    while (data := f.read(BUF)) != b"":
        count = len(data)
        cur_size += count
        f.seek(-count, io.SEEK_CUR)
        f.write(data)
        c -= 1

        if c < 0:
            rate = round(cur_size / (1<<20), 2)
            print(f"进度: {rate}M")
            c = 100


rate = round(cur_size / (1<<20), 2)
print(f"进度: {rate}M")
