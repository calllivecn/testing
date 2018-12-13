#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-13 17:40:49
# author calllivecn <c-all@qq.com>

import io
import os


f = open("5M.logs","wb")

fd = f.fileno()

os.lseek(fd, 5*1024*1024*1024, io.SEEK_CUR)

print(f.tell())
f.seek(-2, io.SEEK_CUR);os.write(fd,b'zx')

f.flush()

os.close(fd)

#f.close()
