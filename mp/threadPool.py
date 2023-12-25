#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-19 15:43:17
# https://github.com/calllivecn

import time
import threading
from random import randint

from concurrent.futures import ThreadPoolExecutor


def f(i):
    t = randint(1, 3)
    c = 0
    start = time.time()

    while True:
        c += 1
        end = time.time()
        if (end - start) >= t:
            break

    return (i, c)



tp = ThreadPoolExecutor(max_workers=4)

def print_thread():
    try:
        while True:
            print(f"当前活动线程数：{threading.active_count()}")
            time.sleep(1)
    except KeyboardInterrupt:
        return 0

th = threading.Thread(target=print_thread, name="这是当前执行的？", daemon=True)
th.start()

for res in tp.map(f, range(40)):
    print(res)

