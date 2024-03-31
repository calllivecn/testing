#!/usr/bin/env python3
# coding=utf-8
# date 2019-10-21 14:46:29
# author calllivecn <calllivecn@outlook.com>

EPSILON = 0.1 ** 10
def newton(x):
    if abs(x ** 2 - 2) > EPSILON:
        return newton(x - (x ** 2 - 2) / (2 * x))
    else:
        return x




print(newton(2))

import math

print(math.sqrt(2))
