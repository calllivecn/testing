#!/usr/bin/env python3
# coding=utf-8
# date 2019-10-23 17:04:01
# author calllivecn <calllivecn@outlook.com>


import time
import random
import asyncio



BASE_DIR="test-dir"


async def delay1(s):
    print(f"delay1 sleep {s} pause")
    await asyncio.sleep(s)
    print(f"delay1 sleep {s} restart")
    return s

async def delay2(s):
    print(f"delay2 sleep {s} pause")
    await asyncio.sleep(s)
    print(f"delay2 sleep {s} restart")
    return s

async def main_gather():

    s = random.randint(1, 5)
    d1 = delay1(s)

    s = random.randint(1, 5)
    d2 = delay2(s)

    results = await asyncio.gather(d1, d2)
    print("results: ", results)


async def main_task():

    s = random.randint(1, 5)
    task1 = asyncio.create_task(delay1(s))

    s = random.randint(1, 5)
    task2 = asyncio.create_task(delay2(s))

    await task1
    await task2

    print("result:", task1.result(), task2.result())


async def main_wait():

    coros = []

    for _ in range(3):
        s = random.randint(1, 5)
        coros.append(delay1(s))

    done, pending = await asyncio.wait(coros)

    print("done:", done)
    print("pending:", pending)



start = time.time()

asyncio.run(main_wait())

end = time.time()

print(f"耗时：{end - start}")
