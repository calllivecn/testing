#!/usr/bin/env python3
# coding=utf-8
# date 2023-11-30 22:31:12
# author calllivecn <c-all@qq.com>

import ctypes
from ctypes import util

class Point(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
    ]

lib = ctypes.CDLL("./add.so")

lib.add2.restype = Point
lib.add2.argtype = [ctypes.c_int, ctypes.c_int]

p = lib.add2(3, 4)
print(f"{p=}, {p.x=}, {p.y=}")

