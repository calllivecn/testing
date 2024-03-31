#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-04 12:16:22
# author calllivecn <calllivecn@outlook.com>

import os
import asyncio

async def nested():
    # return 42
    return os.read(0, 256)

async def main():
    # Nothing happens if we just call "nested()".
    # A coroutine object is created but not awaited,
    # so it *won't run at all*.

    #nested()

    # Let's do it differently now and await it:
    print(await nested())  # will print "42".

asyncio.run(main())
