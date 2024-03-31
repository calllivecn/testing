#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 09:36:01
# author calllivecn <calllivecn@outlook.com>

import asyncio
import time

async def say_after(delay):
    print(delay, "start", end=" ")
    await asyncio.sleep(delay)
    print(delay, "end")

async def say_while(delay, count):
    c = 0 
    while True:
        if c > count:
            # raise ValueError("超出计数了")
            print(delay, "over")
            break
        await say_after(delay)
        c += 1


async def main():

    start = time.time()
    #await asyncio.create_task(say_after(1))
    #await asyncio.create_task(say_after(2))

    # task1 = asyncio.create_task(say_after(1))
    # task2 = asyncio.create_task(say_after(2))

    task1 = asyncio.create_task(say_while(1, 20))
    task2 = asyncio.create_task(say_while(2, 3))


    # 这样只会运行一次进入协程
    # asyncio.gather(say_while(1), say_while(2)) #, return_exceptions=True)

    print("task1 begin...")
    await task1
    print("task1 end...")

    print("task2 begin...")
    await task2
    print("task2 end...")


    print("耗时：{}s".format(round(time.time() - start)))

asyncio.run(main())
