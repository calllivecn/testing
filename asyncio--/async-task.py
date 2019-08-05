#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 09:36:01
# author calllivecn <c-all@qq.com>

import asyncio
import time

async def say_after(delay):
    print(delay, "start")
    await asyncio.sleep(delay)
    print(delay, "end")

async def main():

    start = time.time()
    #await asyncio.create_task(say_after(1))
    #await asyncio.create_task(say_after(2))

    task1 = asyncio.create_task(say_after(1))
    task2 = asyncio.create_task(say_after(2))

    await task1
    await task2
    print("耗时：{}s".format(round(time.time() - start)))

asyncio.run(main())
