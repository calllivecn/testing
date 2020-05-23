#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-13 17:40:49
# author calllivecn <c-all@qq.com>

# 这种方式，没有在磁盘上预申请出指定大小。
# fallocate 命令，或者 #include <fctl.h> int fallocate() 函数。

import io
import os
import ssl

MB = 1 << 20

count = 5 * 1024

f = open("5M.logs","wb")

fd = f.fileno()

f.write(b'zx')
f.flush()

os.lseek(fd, count * MB, io.SEEK_CUR)
print(f.tell())

f.write(b"end")
f.flush()

#for _ in range(count):
#    f.write(ssl.RAND_bytes(MB))
#    f.flush()

f.close()
