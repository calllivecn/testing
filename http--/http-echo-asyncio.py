#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-22 10:54:38
# author calllivecn <c-all@qq.com>


import sys
import random
import asyncio
import argparse


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

    #t = random.randint(100, 3000)/1000
    #await asyncio.sleep(t)

    data = await reader.read(1024)

    if not data:
        return

    writer.write(httpResponse(b"hello world!\n"))
    await writer.drain()


async def handle(reader, writer):

    try:
        await echo(reader, writer)
    except ConnectionResetError:
        pass

    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except ConnectionResetError:
            pass
        

def usage_uvloop():
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ModuleNotFoundError:
        print("需要安装uvloop(pip install --user uvloop)")
        sys.exit(1)



def main():

    parse = argparse.ArgumentParser()
    parse.add_argument("--addr", action="store", default="*", help="listen 地址 (default: ipv4+ipv6)")
    parse.add_argument("--port", action="store", type=int, default=6789, help="port (default: 6789)")
    parse.add_argument("--uvloop", action="store_true", help="使用uvloop")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()

    if args.parse:
        parse.print_usage()
        sys.exit(0)

    if args.uvloop:
        usage_uvloop()
    else:
        print("可以选使用uvloop加速")


    async def server():
        server = await asyncio.start_server(handle, args.addr, args.port, reuse_address=True, reuse_port=True)

        async with server:
            await server.serve_forever()

    print(f"listen: {args.addr}:{args.port}")

    try:
        asyncio.run(server())
    except KeyboardInterrupt:
        print("exit")


if __name__ == "__main__":
    main()