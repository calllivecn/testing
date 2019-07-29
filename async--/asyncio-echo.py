#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 16:57:55
# author calllivecn <c-all@qq.com>

import time
import socket
import asyncio


async def echo(sock):
    #sock.setblocking(False)
    data = sock.recv(4096)
    sock.send(data)
    sock.close()
    #print("client close()")

async def handler():
    pass

async def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind(("127.0.0.1", 6789))
    server.listen(128)

    start = time.time()
    count = 0
    while True:
        client, addr = server.accept()

        #print("client:", addr)
        count += 1
        e = asyncio.create_task(echo(client))
        await e
        end = time.time()
        if (end - start) >= 1:
            print("count: {}/s".format(count))
            start, end = end, time.time()
            count = 0

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
