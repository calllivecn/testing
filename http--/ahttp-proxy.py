#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-09 15:26:026
# author calllivecn <c-all@qq.com>

import asyncio
from functools import partial
from http import HTTPStatus


class RequestError(Exception):
    pass

class MethodError(RequestError):
    pass


class Header:

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        
        self._method = None
        self.request = b""
        self.requestline = b""
        self.requestheaders = b""

        self.host = None
        self.port = None

    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, value):
        if value not in ("GET", "POST", "PUT", "HEAD", "DELETE", "OPTIONS", "CONNECT", "TRACE"):
            self.writer.write(b"HTTP/1.1 400 BAD REQUEST")
            await self.drain()
            raise RequestError("reqeuset method error")

    def getRequestline(self):

        for l in iter(partial(await self.reader.read, 4096), b"\r\n"):

            if l == b"":
                raise RequestError("peer close connection")

            self.requestline += l

            if len(self.request) >= 8192:
                self.conn.send(b"HTTP/1.1 200 REQUEST TOO LONG")
                raise RequestError("request too long")
    
    def parseHost(self):
        requestline = self.request[:self.request.find(b"\r\n")]

        self.method, path, proto = requestline.split(b" ")

        if proto != "HTTP/1.1":
            self.conn.send(HTTPStatus.BAD_GATEWAY)
            raise RequestError("Protocol not is HTTP/1.1")
    
        # 如果是https
        if self.isHttps():
            self.host, self.port = path.decode("ascii").split(":")

        # http
        else:
            self.requestheaders = self.requestline
            for l in iter(partial(await self.reader.read, 4096), b"\r\n\r\n"):

                if l == b"":
                    raise RequestError("peer close connection")

                self.requestheaders += l

            headers = self.requestheaders.split(b"\r\n")[1:]

            for header in headers:
                delimiter = header.find(b":")
                keyname = header[:delimiter]
                if keyname == "Host":
                    value = header[delimiter:].strip(b" ").decode("utf-8")
                    self.host, self.port = value.split(":")
            
            if self.host is None or self.port is None:
                raise RequestError("没有解析到host port")
                

    def isHttps(self):
        if self.method == "CONNECT":
            await self.writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            return True
        else:
            return False
            

async def swap(r1, w1, r2, w2):


async def fisrt(reader, writer):
    data = await reader.read(1024)
    await writer.write(data)


async def proxy(addr, port):
    sock_server = await asyncio.start_server(fisrt, addr, port, limit=1024, reuse_address=True, reuse_port=True)
    addr, port = server.sockets[0].getsockname()
    print("listen:", addr, "port:", port)

    await with sock_server:
        sock_server.serve_forever()



try:
    asyncio.run(proxy())
except KeyboardInterrupt:
    pass