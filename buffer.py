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
    Type,
    TypeVar,
)

class Buffer(bytearray):
    def __init__(self, size: int = 4096):

        super().__init__(size)
        self._mv = memoryview(self)
    
    def __getitem__(self, slice: slice) -> memoryview:
        return self._mv[slice]

    def getvalue(self, start: int = 0, end: Union[int, None] = None) -> bytes:
        return self._mv[start:end].tobytes()


class Buffer2:
    def __init__(self, size: int = 4096, mv: Union[memoryview, None] = None):
    # def __init__(self, size: int = 4096):

        self._size = size
        self._pos = 0


        if isinstance(mv, memoryview):
            self._ba = bytearray(mv)
            self._mv = mv
        else:
            self._ba = bytearray(size)
            self._mv = memoryview(self._ba)
    
    def __getitem__(self, key: slice) -> Type["Buffer2"]:
        buf = Buffer2(key.stop, self._mv[key])
        return buf

    def __setitem__(self, slice_, data):
        self._mv[slice_] = data
    
    def find(self, *args, **kwargs):
        return self._ba.find(*args, **kwargs)
    
    def getvalue(self, start: int = 0, end: Union[int, None] = None) -> bytes:
        return self._mv[start:end].tobytes()


class Buffer3(bytearray):
    def __init__(self, size: int = 4096, mv: Union[memoryview, None] = None):
    # def __init__(self, size: int = 4096):

        self._size = size
        self._pos = 0

        if isinstance(mv, memoryview):
            super().__init__(mv)
            self._mv = mv
        else:
            super().__init__(size)
            self._mv = memoryview(self)
    
    def __len__(self):
        return self._pos
    
    def __getitem__(self, key: slice) -> Type["Buffer3"]:
        buf = Buffer3(key.stop, self._mv[key])
        return buf

    def __setitem__(self, slice_: slice, data: bytes):
        self._pos = slice_.stop
        self._mv[slice_] = data
    
    def getvalue(self, start: int = 0, end: Union[int, None] = None) -> bytes:
        return self._mv[start:end].tobytes()


# data = Buffer2(128)
data = Buffer3(128)
msg = b"CONNECT https://www.google.com\r\nHOST: www.google.com\r\nConnect: keepalive\r\n\r\n"
data[:len(msg)] = msg

print(data.find(b"\r\n"))
print(data.find(b"\r\n\r\n"))

buf = data[:16]
print(f"{data._mv=}\n{buf._mv=}\n{len(data)=}")

print(f"{data.getvalue()=}\n{buf.getvalue()=}")
# print(f"{data._ba=}\t{buf._ba=}")

exit(0)

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
