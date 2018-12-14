#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-13 17:40:49
# author calllivecn <c-all@qq.com>

import io
import os
import ssl

MB = 1 << 20

count = 5 * 1024

f = open("5M.logs","wb")

fd = f.fileno()

os.lseek(fd, count * MB, io.SEEK_CUR)

print(f.tell())
f.seek(-2, io.SEEK_CUR)
os.write(fd,b'zx')
f.flush()

f.seek(0, io.SEEK_SET)
for _ in range(count):
    f.write(ssl.RAND_bytes(MB))
    f.flush()

os.close(fd)

#f.close()
