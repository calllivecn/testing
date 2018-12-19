#!/usr/bin/env python3
#coding=utf-8
# date 2018-06-20 00:21:57
# author calllivecn <c-all@qq.com>


import sys
import math

a, b, c = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])


def area(a, b, c):
    s = 0.5 * (a + b + c)
    return math.sqrt(s * (s-a) * ( s-b) * (s-c))


if __name__ == "__main__":
    S = area(a, b, c)
    print(S)
