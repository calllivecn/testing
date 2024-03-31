#!/usr/bin/env python3
# coding=utf-8
# date 2022-06-10 02:26:28
# author calllivecn <calllivecn@outlook.com>

import sys

import numpy as np
import numba as nb



#@nb.jit(nopython=True)
def add(i):
    c = 0
    while c <= i:
        c += 1
    return c


n = int(sys.argv[1])

print(add(n))
