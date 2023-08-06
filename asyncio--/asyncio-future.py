#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-06 13:35:11
# author calllivecn <c-all@qq.com>

import asyncio

PORT = 6789

def client(port):
    pass


async def another_coroutine():
    print("手动添加成功")


def manual_add():
    print('手动添加一个协程到当前loop')
    # loop = asyncio.get_running_loop()
    asyncio.ensure_future(another_coroutine())


async def my_coroutine():
    print('My coroutine')
    manual_add()

asyncio.run(my_coroutine())
