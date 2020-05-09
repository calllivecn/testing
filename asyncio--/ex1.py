#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-10 00:23:20
# author calllivecn <c-all@qq.com>


import asyncio


async def print_hello():
    #for i in range(5):
    while True:
        print("hello name")
        await asyncio.sleep(1)

async def secd():
    #for i in range(7):
    while True:
        print("sleep 2")
        asyncio.sleep(2)

async def main():
    print_hello()
    secd()

loop = asyncio.get_event_loop()

#print(dir(loop))

loop.util_loop_()

#asyncio.main()
