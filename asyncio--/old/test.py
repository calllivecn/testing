#!/usr/bin/env py3
#coding=utf-8
# date 2018-08-25 00:30:53
# author calllivecn <c-all@qq.com>

import asyncio

class ThreeTwoOne:
    async def begin(self):
        print(3)
        await asyncio.sleep(1)
        print(2)
        await asyncio.sleep(1)
        print(1)
        await asyncio.sleep(1)

async def game():
    t = ThreeTwoOne()
    await t.begin()
    print('start')

asyncio.run_loop(game())
