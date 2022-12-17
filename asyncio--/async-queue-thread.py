#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-14 14:46:45
# author calllivecn <c-all@qq.com>

import time
import queue
import asyncio
import threading


async def get_print(q):
    while True:
        text = await q.get()

        # 这样执行到这时会阻塞
        # text = q.get()

        print("async get():", text)
        await asyncio.sleep(1)


def run_asyncio_in_pthread(q):
    asyncio.run(get_print(q))


def pthread():
    # q = queue.Queue(2)
    q = asyncio.Queue(2)

    th1 = threading.Thread(target=run_asyncio_in_pthread, args=(q,), daemon=True)
    th1.start()

    for c in range(10):
        q.put(c)
        print("put():", c)
        c+=1
        time.sleep(0.2)
    
    q.join()

try:
    pthread()
except KeyboardInterrupt:
    pass
