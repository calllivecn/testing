#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 16:57:55
# author calllivecn <c-all@qq.com>

import time
import socket
import asyncio

BLOCK = 1<<14 # 16k

async def echo(reader, writer):
    while True:
        try:
            data = await reader.read(BLOCK)
        except ConnectionResetError:
            break

        if not data:
            break

        writer.write(b"Got: " + data)
        #print("data:", data)
        await writer.drain()

    writer.close()
    await writer.wait_closed()
    #print("client close()")


async def main():
    server = await asyncio.start_server(echo, "0.0.0.0", 6789, reuse_address=None, reuse_port=None)

    addr = server.sockets[0].getsockname()
    print("listen:", addr)

    async with server:
        await server.serve_forever()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
