#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-19 15:18:37
# https://github.com/calllivecn

import multiprocessing as mp

import time
import random

def f(x):
    t = random.randint(1,4)
    time.sleep(t)
    return x, t

pool = mp.Pool()

print(pool.map(f, range(10)))

