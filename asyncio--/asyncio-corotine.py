#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-01 15:03:58
# author calllivecn <c-all@qq.com>


import asyncio

async def nested():
    return 42

async def main():

    #nested()

    print(await nested())


asyncio.run(main())
