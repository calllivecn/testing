#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-14 10:56:05
# author calllivecn <calllivecn@outlook.com>

import time
import asyncio
import threading
from datetime import datetime

def my_func():
    for i in range(3):
        print("sleep(1)")
        time.sleep(1)
    return datetime.now()

async def fetch_async(func, *args, **kwargs):
    print("begin")
    #loop = asyncio.get_event_loop()
    loop = asyncio.get_running_loop()

    # 这个方法是在后台起了一个线程实现的。
    future = loop.run_in_executor(None, func, *args, **kwargs)
    result = await future
    return result

tasks = [
    fetch_async(my_func),
    fetch_async(my_func),
]

tasks2 = [
    fetch_async(my_func),
    fetch_async(my_func),
    fetch_async(my_func),
]

tasks3 = [
    fetch_async(my_func),
    fetch_async(my_func),
    fetch_async(my_func),
]

tasks4 = [
    fetch_async(my_func)
]

async def main():
    result_list = await asyncio.gather(*tasks)
    th_list = threading.enumerate()
    print("运行完后：len(threads):", len(th_list))
    
    result_list = await asyncio.gather(*tasks2)
    th_list = threading.enumerate()
    print("运行完后：len(threads):", len(th_list))

    result_list = await asyncio.gather(*tasks3)
    th_list = threading.enumerate()
    print("运行完后：len(threads):", len(th_list))

    result_list = await asyncio.gather(*tasks4)
    th_list = threading.enumerate()
    print("运行完后：len(threads):", len(th_list))

    return result_list

"""
# 新版 不这样了。
loop = asyncio.get_event_loop()
results = loop.run_until_complete(asyncio.gather(*tasks))
print(results)
loop.close()
"""

th_list = threading.enumerate()
print("运行前：len(threads):", len(th_list))

results = asyncio.run(main())
print(results)
