#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 10:54:38
# author calllivecn <c-all@qq.com>


import asyncio


def httpResponse(msg):
    response = [
            "HTTP/1.1 200 ok",
            "Server: py",
            "Content-Type: text/plain",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    return "\r\n".join(response).encode("utf8") + msg


async def echo(reader, writer):

    try:
        data = await reader.read(1024)
    except ConnectionResetError:
        return

    if not data:
        return

    writer.write(httpResponse(b"hello world!\n"))
    #await writer.drain()
    writer.close()
    #await writer.wait_closed()


addr = "0.0.0.0"
port = 6785

async def server():
    server = await asyncio.start_server(echo, addr, port, limit=(1<<10), reuse_address=True, reuse_port=True)

    async with server:
        await server.serve_forever()

print(f"listen: {addr}:{port}")

try:
    asyncio.run(server())
except KeyboardInterrupt:
    print("exit")
