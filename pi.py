#!/usr/bin/env python3
# coding=utf-8
# date 2019-06-11 09:39:40
# author calllivecn <c-all@qq.com>

import sys
import math
import decimal


def pi(n):
    PI = 0.0

    for i in range(n):
        PI += 1/pow(16, i) * (4/(8*i + 1) - 2/(8*i + 4) - 1/(8*i + 5) - 1/(8*i +6))

    return PI

def pi2(n):
    decimal.getcontext().prec = 128
    PI = decimal.Decimal("0.0")

    for i in range(n):
        i = decimal.Decimal(i)
        PI += 1/pow(16, i) * (4/(8*i + 1) - 2/(8*i + 4) - 1/(8*i + 5) - 1/(8*i +6))

    return PI

if __name__ == "__main__":
    try:
        N = int(sys.argv[1])
    except Exception:
        N = 5000

    print(f"PI({N}) --> {pi2(N)}")
