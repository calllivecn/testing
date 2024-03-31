#!/usr/bin/env python3
# coding=utf-8
# date 2020-03-12 19:53:17
# author calllivecn <calllivecn@outlook.com>

import os
import sys
import time
import logging
import multiprocessing as mp
from logging import handlers


que = mp.Queue(-1)

queue_handler = handlers.QueueHandler(que)

handler = logging.StreamHandler()

listener = handlers.QueueListener(que, handler)

logger = logging.getLogger()

fmt = logging.Formatter("%(asctime)s.%(msecs)d %(thread)s %(message)s", datefmt="%Y-%m-%d-%H:%M%S")

handler.setFormatter(fmt)

handler.setLevel(logging.DEBUG)

logger.addHandler(queue_handler)

logger.setLevel(logging.DEBUG)


def worker(que):
    c = 0
    pid = os.getpid()
    while True:
        c += 1
        msg = f"PID:{pid} MSG:{c}"
        logger.debug(msg)
        time.sleep(0.01)


listener.start()

workers = []

for _ in range(4):
    subproc = mp.Process(target=worker, args=(que,), daemon=True)
    subproc.start()
    workers.append(subproc)



print("当前日志等级：", logger.level)
print("sleep(10)")
time.sleep(10)

print("关闭子进程")
for subproc in workers:
    subproc.terminate()

listener.stop()
