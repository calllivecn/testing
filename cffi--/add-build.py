#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 01:07:13
# author calllivecn <calllivecn@outlook.com>

import os

from cffi import FFI
ffibuilder = FFI()

# cdef() expects a single string declaring the C types, functions and
# globals needed to use the shared object. It must be in valid C syntax.
ffibuilder.cdef("""
    typedef struct Point;
    int add(int a, int b);
    Point add2(Point a, Point b);
""")


lib = ffibuilder.dlopen("libadd.so")

print(lib.add(4, 5))

a = ffibuilder.new("Point", {"x": 5, "y": 6})
print(a.x, a.y)



# set_source() gives the name of the python extension module to
# produce, and some C source code as a string.  This C code needs
# to make the declarated functions, types and globals available,
# so it is often just the "#include".

#ffibuilder.set_source("_add_cffi",
#    """
#    #include "add.h"
#    """,
#    libraries=['add'],
#    include_dirs=[os.getcwd()],
#    library_dirs=[os.getcwd()]   # library name, for the linker
#    )
#
#if __name__ == "__main__":
#    ffibuilder.compile(verbose=True)
