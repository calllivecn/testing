#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 09:17:49
# author calllivecn <calllivecn@outlook.com>


import sys
import time
import asyncio 

async def process_input(fp):
    print(">>> ",end="")
    text = fp.readline()
    text.strip()
    print("\nyour input: {}".format(text))

async def timer(end):
    if end >= 3:
        print("{} Hello ~".format(time.time()))
    else:
        print("时间没到3秒钟")

async def main():
    while True:
        end = time.time()
        await asyncio.create_task(timer(time.time() - end))
        await asyncio.create_task(process_input(sys.stdin))
        print("执行完一个主循环。")


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
