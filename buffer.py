#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-13 05:10:10
# author calllivecn <c-all@qq.com>


import io
import sys
import ssl
import hashlib
import time

from typing import (
    Union,
    Iterable,
)

class Buffer(bytearray):
    def __init__(self, size: int = 4096):

        super().__init__(size)
        # self._ba = bytearray(size)
        self._mv = memoryview(self)
    
    def __getitem__(self, slice: slice) -> memoryview:
        return self._mv[slice]
    
    def getvalue(self, start: int = 0, end: Union[int, None] = None) -> bytes:
        return self._mv[start:end].tobytes()


# data = Buffer(128)

SIZE = 10*(1<<20)
SIZE = (1<<13) # 8k
SIZE = (1<<14) # 16k

# buf = memoryview(bytearray(SIZE))
# 并不能提高性能。。。。
# 看看使用这种方式是不是会省内存。 是省内存，省了差不多一半。 SIZE 为 16k 时，运行速度最快。

if __name__ == "__main__":
    buf = Buffer(SIZE)
    sha = hashlib.sha256()
    with open(sys.argv[1], "rb") as f:
        while (n := f.readinto(buf)) != 0:
            sha.update(buf[:n])

        print(sha.hexdigest())
