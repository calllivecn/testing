#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 16:57:55
# author calllivecn <calllivecn@outlook.com>

import time
import socket
import asyncio

BLOCK = 1<<14 # 16k

async def echo(sock):
    while True:
        try:
            data = await loop.sock_recv(sock, BLOCK)
        except ConnectionResetError:
            break

        if not data:
            break

        await loop.sock_sendall(sock, b"Got: " + data)
        #print("data:", data)

    sock.close()
    #print("client close()")


async def main():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 6789))
    server.listen(128)

    server.setblocking(False)

    start = time.time()
    count = 0
    while True:
        #client, addr = server.accept()
        client, addr = await loop.sock_accept(server)

        #print("client:", addr)
        client.setblocking(False)
        loop.create_task(echo(client))

        interval = time.time() - start
        if interval >= 1:
            start = time.time()
            print("并发速度：", count, "/s")
            count = 0
        else:
            count += 1


loop = asyncio.get_event_loop()
loop.create_task(main())

try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

finally:
    loop.close()
