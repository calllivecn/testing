#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-13 20:31:19
# author calllivecn <c-all@qq.com>

# 这是3.11 才有的

import asyncio

async def main():
    try:
        async with asyncio.timeout(3):
            # await long_running_task()
            await asyncio.sleep4(4)
    except TimeoutError:
        print("The long operation timed out, but we've handled it.")

    print("This statement will run regardless.")

asyncio.run(main())