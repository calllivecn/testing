#!/usr/bin/env python3
# coding=utf-8
# date 2022-11-06 03:47:03
# author calllivecn <c-all@qq.com>


import time
from concurrent.futures import (
    Executor,
)

def run():
    print("任务开始")
    time.sleep(5)
    print("任务结束")

e = Executor()

future = e.submit(run)

e.shutdown()
