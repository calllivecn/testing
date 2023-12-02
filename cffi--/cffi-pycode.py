#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-03 01:07:13
# author calllivecn <c-all@qq.com>

import os

from cffi import FFI
ffibuilder = FFI()

# cdef() expects a single string declaring the C types, functions and
# globals needed to use the shared object. It must be in valid C syntax.
ffibuilder.cdef("""
    int add(int a, int b);
""")

# set_source() gives the name of the python extension module to
# produce, and some C source code as a string.  This C code needs
# to make the declarated functions, types and globals available,
# so it is often just the "#include".
ffibuilder.set_source("_add_cffi",
"""
     #include "add.c"   // the C header of the library
""",
     libraries=['add'],library_dirs=[os.getcwd()])   # library name, for the linker

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
