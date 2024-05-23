#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-12 21:38:38
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import time


# ok
def test_ok():
    try:
        import setproctitle
    except Exception:
        raise ModuleNotFoundError("需要 setproctitle 库")

    setproctitle.setproctitle("使用中文进程名")


# 还是不行
def test_zx():
    import ctypes
    libc = ctypes.CDLL("libc.so.6")
    #print(dir(libc))
    #sys.exit(0)

    #参数2：15 /linux/prctl.h定义  #define PR_SET_NAME    15 
    PR_SET_NAME = 15
    PR_GET_NAME = 16

    new_name = "myproc"

    #libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_char)
    libc.prctl.restypes = ctypes.c_int

    #c_ulong_new_name = ctypes.cast(ctypes.create_unicode_buffer(new_name), ctypes.c_ulong)
    libc.prctl(PR_SET_NAME, new_name) #执行后ps -A,显示为myproc的进程


# 使用第三方库是可以
test_ok()
#test_zx()

print("pid:", os.getpid())

#time.sleep(30)
input("按回车退出")
