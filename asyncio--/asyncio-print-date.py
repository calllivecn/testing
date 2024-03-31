#!/usr/bin/env python3
# coding=utf-8
# date 2019-10-22 17:29:42
# author calllivecn <calllivecn@outlook.com>

import asyncio
import datetime

async def display_date():
    loop = asyncio.get_running_loop()
    end_time = loop.time() + 5.0
    while True:
        print(datetime.datetime.now())
        if (loop.time() + 1.0) >= end_time:
            break
        await asyncio.sleep(1)

asyncio.run(display_date())
