#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 01:20:44
# author calllivecn <calllivecn@outlook.com>

from cffi import FFI

ffi = FFI()

lib = ffi.dlopen("./libadd.so")

ffi.cdef("""

typedef struct {
    int x;
    int y;
} Point;

int add(int, int);
Point add2(Point, Point);

""")

print(lib.add(3, 5))

# 这种直接创建结构体的方式还不行，v1.16.0
#a = ffi.new("Point", [4, 5])

# 需要这样直接创建结构体
a = ffi.new("Point*", [4, 5])[0]
b = ffi.new("Point*", [4, 5])[0]

print(f"{a=}")

a = lib.add2(a, b)

print(f"{a.x=} {a.y=}")



