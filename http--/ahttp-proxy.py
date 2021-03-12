#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-09 15:26:026
# author calllivecn <c-all@qq.com>

import sys
import asyncio
import logging
from functools import partial
from http import HTTPStatus
from argparse import ArgumentParser


def getlogger():
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",datefmt="%Y-%m-%d-%H:%M:%S")
    handler.setFormatter(fmt)

    logger = logging.getLogger("http proxy")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


logger = getlogger()

class RequestError(Exception):
    pass

class MethodError(RequestError):
    pass

class HostPostError(RequestError):
    pass

class Header:

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        
        self._method = None
        self.buffer = b""
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

    async def getRequest(self):

        while True:
            buffer = await self.reader.read(4096)

            if buffer == b"":
                raise RequestError("peer close connection")

            self.buffer += buffer

            self.delimiter = self.buffer.find(b"\r\n\r\n")
            if self.delimiter != -1:
                break


            if len(self.buffer) >= 8192:

                self.writer.write(b"HTTP/1.1 200 REQUEST TOO LONG")
                await self.writer.drain()
                self.writer.close()

                raise RequestError("request too long")

        # 这里可以 把 request line 分离出来了
        self.headers = self.buffer[:self.delimiter].decode("ascii")

        logger.debug(f"self.headers ==> {self.headers}")

        self.method = self.headers[:self.headers.find(" ")]
    
    def isHttps(self):
        if self.method.upper() == "CONNECT":
            return True
        else:
            return False
            
    def data(self):
        if self.isHttps():
            return self.buffer[self.delimiter + 4:]
        else:
            return self.buffer
    
    async def get_Host_Port(self):

        # 如果是https 否则是 http
        if self.isHttps():

            https_line = self.headers.split("\r\n")[0]
            logger.debug(f"https_line ==> {https_line}")

            method, host_port, protocol = https_line.split(" ")

            if ":" in host_port:
                self.host, self.port = host_port.split(":")
                self.port = int(self.port)
            else:
                self.host = host_port
                self.port = 443


        else:

            for header in self.headers.split("\r\n"):

                if header.startswith("Host:") or header.startswith("HOST:") or header.startswith("host:"):
                    
                    host_port = header.split(":")
                    if len(host_port) == 2:
                        self.host = host_port[1].strip(" ")
                        self.port = 80

                    elif len(host_port) == 3:
                        self.host = host_port[1].strip(" ")
                        self.port = int(host_port[2].strip(" "))
                    else:
                        logger.warning("host: port 解析错误。")
                        raise HostPostError("host: port 解析错误。")
            
        if self.host is None or self.port is None:
            raise RequestError("没有解析到host port")
        


async def swap(r1, w2):
    logger.debug(f"id: {id(r1)}")
    while True:
        data = await r1.read(4096)

        if not data:
            break

        try:
            i = w2.write(data)
            await w2.drain()
        except ConnectionResetError:
            w2.close()
            break
    
    if not w2.is_closing():
        w2.close()

async def handle(reader, writer):

    try:
        head = Header(reader, writer)
        await head.getRequest()
        await head.get_Host_Port()
    except Exception as e:
        logger.warning(f"异常： {e}")
        writer.close()
        return

    r2, w2 = await asyncio.open_connection(head.host, head.port, limit=4096)

    if head.isHttps():
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()
    else:
        logger.debug(f"head.data ==> {head.data()}")
        w2.write(head.data())
        await w2.drain()

    # 我去， 这里必需是分开的 task 不然不是并发的....
    task1 = asyncio.create_task(swap(reader, w2))
    task2 = asyncio.create_task(swap(r2, writer))
    await task1 
    await task2 

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
    else:
        logger.setLevel(logging.INFO)

    sock_server = await asyncio.start_server(handle, args.addr, args.port, limit=4096, reuse_address=True, reuse_port=True)

    # addr, port = sock_server.sockets[0].getsockname()
    print("listen:", args.addr, "port:", args.port)

    async with sock_server:
        await sock_server.serve_forever()


try:
    asyncio.run(proxy())
except KeyboardInterrupt:
    pass
