#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-29 16:57:55
# author calllivecn <c-all@qq.com>

import time
import socket
import asyncio

BLOCK = 1<<14 # 16k

async def echo(sock):
    while True:
        data = await loop.sock_recv(sock, BLOCK)
        if not data:
            break

        await loop.sock_sendall(sock, b"Got: " + data)

    sock.close()
    print("client close()")


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

        print("client:", addr)
        client.setblocking(False)
        loop.create_task(echo(client))


loop = asyncio.get_event_loop()


try:
    loop.create_task(main())
    loop.run_forever()
except KeyboardInterrupt:
    pass

finally:
    loop.close()
