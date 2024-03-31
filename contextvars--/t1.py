#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-14 02:18:00
# author calllivecn <calllivecn@outlook.com>

import asyncio
import contextvars

# 申明Context变量
request_id = contextvars.ContextVar('Id of request')


async def get():
    # Get Value
    print(f'Request ID (Inner): {request_id.get()}')


async def new_coro(req_id):
    # Set Value
    request_id.set(req_id)
    await get()
    print(f'Request ID (Outer): {request_id.get()}')


async def main():
    tasks = []
    for req_id in range(1, 5):
        tasks.append(asyncio.create_task(new_coro(req_id)))

    await asyncio.gather(*tasks)


asyncio.run(main())
