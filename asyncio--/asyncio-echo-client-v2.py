#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-10 02:44:43
# author calllivecn <calllivecn@outlook.com>

import time
import asyncio



async def echo_client(msg):
    #await asyncio.sleep(1)
    r, w = await asyncio.open_connection("127.0.0.1", 6789)
    #print(f"Send: {msg}")

    w.write(msg.encode())
    await w.drain()

    data = await r.read(4096)
    #print(f"Recv: {data.decode()}")
    w.close()
    await w.wait_closed()


async def main(count):
    for i in range(count):
        await echo_client(f"{i}: echo message!")
    

count = 5000
print(f"执行{count}次, echo 请求")
start = time.time()

asyncio.run(main(count))

speed = count / (time.time() - start)
print(f"{speed}/s")
