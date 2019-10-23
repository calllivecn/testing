#!/usr/bin/env python3
# coding=utf-8
# date 2019-10-22 16:00:00
# author calllivecn <c-all@qq.com>

import time
import asyncio


# 1.

#async def main():
#    print("hello")
#    await asyncio.sleep(1)
#    print("world")
#
#
#asyncio.run(main())


# 2. 不会减少耗时, 3s

#async def say_after(delay, what):
#    await asyncio.sleep(delay)
#    print(what)
#
#
#
#async def main():
#    start = time.time()
#
#    await say_after(1, "hello")
#    await say_after(2, "world")
#
#    print("started at:", time.time() - start, "/s")
#
#asyncio.run(main())


# 3. 使用task，后减少耗时

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)



async def main():
    start = time.time()

    task1 = asyncio.create_task(say_after(1, "hello"))
    task2 = asyncio.create_task(say_after(2, "world"))

    await task1
    await task2

    print("started at:", time.time() - start, "/s")

asyncio.run(main())
