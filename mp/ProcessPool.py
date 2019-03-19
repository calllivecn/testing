#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-19 15:43:17
# https://github.com/calllivecn

import time
import threading
from random import randint

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


def f(i):
    t = randint(3, 10)
    c = 0
    start = time.time()

    while True:
        c += 1
        end = time.time()
        if (end - start) >= t:
            break

    return (i, c)



#tp = ThreadPoolExecutor(max_workers=4)
pp = ProcessPoolExecutor(max_workers=4)

def print_thread():
    try:
        while True:
            print(threading.active_count())
            time.sleep(1)
    except KeyboardInterrupt:
        return 0


#for res in pp.map(f, range(10)):
#    print(res)
res = [ d for d in pp.map(f, range(10)) ]
pp.shutdown()

print(res)

