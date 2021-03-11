#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-09 15:26:026
# author calllivecn <c-all@qq.com>

import sys
import asyncio
from functools import partial
from http import HTTPStatus
from argparse import ArgumentParser


class RequestError(Exception):
    pass

class MethodError(RequestError):
    pass


class Header:

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        
        self._method = None
        self.buffer = b""
        self.requestline = b""
        self.requestheaders = b""
        self.delimiter = 0

        self.host = None
        self.port = None

    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, value):
        self._method = value

    async def getRequestline(self):

        buffer = b""

        while True:
            buffer += await self.reader.read(4096)

            if buffer == b"":
                raise RequestError("peer close connection")

            self.buffer += buffer

            self.delimiter = self.buffer.find(b"\r\n")
            if self.delimiter != -1:
                break


            if len(self.buffer) >= 8192:

                self.self.writer.write(b"HTTP/1.1 200 REQUEST TOO LONG")
                await self.writer.drain()
                self.writer.close()

                raise RequestError("request too long")

        # 这里可以 把 request line 分离出来了
        self.requestline = self.buffer[:self.delimiter]
    
    def isHttps(self):
        if self.method == "CONNECT":
            return True
        else:
            return False
            
    async def parseHost(self):

        self.method, path, proto = self.requestline.decode("ascii").split(" ")

        if proto != "HTTP/1.1":
            self.writer.write(HTTPStatus.BAD_GATEWAY)
            await self.writer.drain()
            self.writer.close()
            raise RequestError("Protocol not is HTTP/1.1")
    
        # 如果是https 否则是 http
        if self.isHttps():
            await self.writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            try:
                self.host, self.port = path.split(":")
            except ValueError:
                self.port = 443
        else:
            self.requestheaders = self.buffer[self.delimiter:]

            while True:
                buffer = await self.reader.read(4096)

                if buffer == b"":
                    raise RequestError("peer close connection")

                self.requestheaders += buffer

                self.delimiter_header = self.requestheaders.find(b"\r\n\r\n")
                if self.delimiter_header != -1:
                    break


                if len(self.requestheaders) >= 8192:

                    self.self.writer.write(b"HTTP/1.1 200 REQUEST TOO LONG")
                    await self.writer.drain()
                    self.writer.close()

                    raise RequestError("request too long")

                self.requestheaders += buffer

            headers = self.requestheaders[:self.delimiter_header].decode("ascii")

            for header in headers:
                delimiter = header.find(":")
                keyname = header[:delimiter]
                if keyname.upper() == "HOST":
                    value = header[delimiter:].strip(" ")
                    try:
                        self.host, self.port = value.split(":")
                    except ValueError:
                        self.port = 80
            
            if self.host is None or self.port is None:
                raise RequestError("没有解析到host port")
        
        #async def writeclose(self, data):
        #    self.writer.write(data)
        #    await self.writer
        #        

async def swap(r1, w1, r2, w2):
    while True:
        data = await r1.read(4096)

        if not data:
            w1.close()
            break

        try:
            i = w2.write(data)
            await w2.drain()
        except ConnectionResetError:
            w2.close()
            break
    
    if not w1.is_closing():
        w1.close()

    if not w2.is_closing():
        w2.close()

async def fisrt(reader, writer):

    try:
        head = Header(reader, writer)
        await head.getRequestline()
        await head.parseHost()
    except Exception as e:
        print("异常：", e)
        writer.close()
        return

    r2, w2 = await asyncio.open_connection(head.host, head.port, limit=4096)

    await swap(reader, writer, r2, w2)


async def proxy():
    parse = ArgumentParser(
        description="一个用asyncio实现的http https代理服务器。",
        usage="[ --addr <0.0.0.0>|<::> <*>] [--port <8080>]",
        epilog="callivecn 编写"
    )

    parse.add_argument("--addr", default="*", help="指定监听地址，同时监听ipv4 ipv6")
    parse.add_argument("--port", type=int, default=8080, help="指定监听端口default: 8080")
    parse.add_argument("--debug", action="store_true", help="--debug")

    args = parse.parse_args()

    if args.debug:
        print(args)
        sys.exit(0)

    sock_server = await asyncio.start_server(fisrt, args.addr, args.port, limit=4096, reuse_address=True, reuse_port=True)

    # addr, port = sock_server.sockets[0].getsockname()
    print("listen:", args.addr, "port:", args.port)

    async with sock_server:
        await sock_server.serve_forever()


try:
    asyncio.run(proxy())
except KeyboardInterrupt:
    pass