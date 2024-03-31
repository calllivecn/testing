#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-12 21:38:38
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import time

try:
    import setproctitle
except Exception:
    raise ModuleNotFoundError("需要 setproctitle 库")

import ctypes
libc = ctypes.CDLL("libc.so.6")
#print(dir(libc))
#sys.exit(0)
PR_SET_NAME = 15
PR_GET_NAME = 16
#libc.prctl(PR_SET_NAME, 'myproc', 0, 0, 0) #执行后ps -A,显示为myproc的进程
#libc.prctl.argtypes = (ctypes.c_int, ctypes.c_char_p)
#libc.prctl.restype = ctypes.c_int
#print(libc.prctl(PR_SET_NAME, b'myproc'))
#参数2：15 /linux/prctl.h定义  #define PR_SET_NAME    15 

setproctitle.setproctitle("使用中文进程名")

print("pid:", os.getpid())

#time.sleep(30)
input("按回车退出")
