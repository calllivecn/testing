#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 09:36:01
# author calllivecn <c-all@qq.com>

import asyncio
import time

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():


    print(f"started at {time.strftime('%X')}")
    start = time.time()
    await asyncio.create_task(say_after(1, 'hello'))
    await asyncio.create_task(say_after(2, 'world'))

    #task1 = asyncio.create_task(say_after(1, 'hello'))
    #task2 = asyncio.create_task(say_after(2, 'world'))

    #await task1
    #await task2
    print(f"finished at {time.strftime('%X')}")

    print("耗时：{}s".format(time.time() - start))

asyncio.run(main())
