#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-09 21:21:12
# author calllivecn <c-all@qq.com>


import queue
import asyncio
import threading


async def customer(q):
    while True:
        # task = await q.get()
        task = q.get()
        q.task_done()
        print(f"customer: {task}")


def customer2(q):
    while True:
        task = q.get()
        q.task_done()
        print(f"customer: {task}")

def producter(q):
    for i in range(10):
        c = f"生产资料：{i}"
        # await q.put(c)
        q.put(c)
        print(c)


class asyncio_run(threading.Thread):
    def __init__(self, queue):
        super().__init__()

        self.queue = queue

    def run(self):
        asyncio.run(customer(self.queue))


class run(threading.Thread):
    def __init__(self, queue):
        super().__init__()

        self.queue = queue

    def run(self):
        asyncio.run(customer2(self.queue))


# q = asyncio.Queue(16)
q = queue.Queue(16)

print("启动消费者")
# th = run(q)
th = asyncio_run(q)
th.start()

print("启动生产者")
producter(q)
