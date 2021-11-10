#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 16:57:55
# author calllivecn <c-all@qq.com>

import sys
import asyncio

BLOCK = 1<<14 # 16k

async def echo(reader, writer):

    addr = writer.transport.get_extra_info("peername")
    print("client addr:", addr)


    while True:

        try:
            data = await asyncio.wait_for(reader.read(BLOCK), timeout=5)
        except asyncio.exceptions.TimeoutError:
            print("client timeout")
            break

        if not data:
            break

        try:
            writer.write(b"Got: " + data)
        except ConnectionResetError:
            print("peer reset connection", file=sys.stderr)
            break

        #print("data:", data)
        await writer.drain()

    writer.close()
    await writer.wait_closed()
    #print("client close()")


async def main():
    server = await asyncio.start_server(echo, "0.0.0.0", 6789, reuse_address=None, reuse_port=None)

    addr, port = server.sockets[0].getsockname()
    print("listen:", addr, "port:", port)

    async with server:
        await server.serve_forever()


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
