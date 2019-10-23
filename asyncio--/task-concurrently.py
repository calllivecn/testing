#!/usr/bin/env python3
# coding=utf-8
# date 2019-10-22 17:38:05
# author calllivecn <c-all@qq.com>


import asyncio


async def factorial(name, number):
    f = 1

    for i in range(2, number+1):
        print(f"task {name}: Compute factorial({i})")
        await asyncio.sleep(0.5)
        f *= i
    print(f"task {name}: factorial({i}) = {f}")


async def main():

    await asyncio.gather(
            factorial("A", 4),
            factorial("B", 7),
            factorial("C", 9),
            )


asyncio.run(main())

