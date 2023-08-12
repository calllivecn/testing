#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-09 21:21:12
# author calllivecn <c-all@qq.com>


import queue
import asyncio
import threading


async def customer(q):
    while (task := await q.get()) is not None:
        q.task_done()
        print(f"customer: {task}")


async def producter(q):
    for i in range(10):
        c = f"生产资料：{i}"
        await q.put(c)
        print(c)

    await q.put(None)


def customer2(q):
    while (task := q.get()) is not None:
        q.task_done()
        print(f"customer: {task}")


def producter2(q):
    for i in range(10):
        c = f"生产资料：{i}"
        q.put(c)
        print(c)

    q.put(None)


class run(threading.Thread):
    def __init__(self, queue):
        super().__init__()

        self.queue = queue

    def run(self):
        customer2(self.queue)


async def async_main():
    q = asyncio.Queue(2)
    print("启动消费者")
    th = asyncio.create_task(customer(q))
    print("启动生产者")
    p = asyncio.create_task(producter(q))

    # 这样才是并发的
    await th
    print("这是在 消费者后面")
    await p
    print("这是在 生产者后面")

async def async_main2():
    q = asyncio.Queue(2)
    print("启动消费者")
    print("启动生产者")
    L = await asyncio.gather(customer(q), producter(q))
    print("结果：", L)

def main():
    q = queue.Queue(2)
    print("启动消费者")
    th = run(q)
    th.start()
    print("启动生产者")
    producter2(q)


if __name__ == "__main__":
    asyncio.run(async_main())
    # asyncio.run(async_main2())
    # main()