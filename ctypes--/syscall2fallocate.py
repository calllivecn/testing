#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-26 23:33:12
# author calllivecn <c-all@qq.com>

import errno
import ctypes

from ctypes import (
                    c_int,
                    c_uint64
                    )


libc = ctypes.CDLL("libc.so.6", use_errno=True)

print(f"通过libc.syscall() 调用 getpid() 系统调用拿到pid: {libc.syscall(39)}")


def fallocate(fd, length, offset=0):
    __NR_fallocate = 47

    FALLOC_FL_KEEP_SIZE = 0x01
    FALLOC_DEFAULT = 0x00

    MODE = c_int(FALLOC_DEFAULT)

    OFFSET = c_int(offset)
    LEN = c_int(length)

    libc.syscall.argtype = (c_int, c_int, c_int, c_uint64, c_uint64)
    libc.syscall.restype = c_int

    result = libc.syscall(__NR_fallocate, MODE, OFFSET, LEN)

    if result != 0:
        print("syscall fallocate Error")
        err = ctypes.get_errno()

        print(errno.errorcode[err])
        print(f"ERR: {result}")
        return False
    else:
        return True


f_10G = 1*(1<<30)

print("fallocate 一个10G的文件")

with open("fallocate.1G", "wb") as f:
    fallocate(f.fileno(), f_10G)



