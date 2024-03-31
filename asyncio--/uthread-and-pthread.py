#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-23 22:43:22
# author calllivecn <calllivecn@outlook.com>


import time
import asyncio
from threading import Thread



async def loop():
    c=0
    while True:
        print("asyncio:", c)
        c+=1
        await asyncio.sleep(1)


def run_asyncio_in_pthread():
    asyncio.run(loop())


th1 = Thread(target=run_asyncio_in_pthread)
th1.start()

def pthread():
    c=0
    while True:
        print("pthread:", c)
        c+=1
        time.sleep(1)

try:
    pthread()
except KeyboardInterrupt:
    pass
