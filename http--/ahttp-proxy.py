#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-09 15:26:026
# author calllivecn <c-all@qq.com>

import asyncio
from functools import partial

"""
感觉需要设计一个，从流中接收数据的站class。
1. 以一个最大block接收数据，
2. 从里面可以以一个分隔符拿到分隔符前面的数据。
3. 可以查看还有没有剩下的数据is_empty() --> bool。
"""

class StreamStack:

    def __init__(self, conn, block=4096):
        self.conn = conn
        self.block = block
        self.stack = b""
    
    def read(self):
        """
        从流中读取一次数据到站。
        """
        data = self.conn.recv(self.block)
        if not data:
            raise PeerClose("peer close this connection.")
        
        self.stack += data
    
    def write(self, data):
        return self.conn.send(data)
    
    def is_delimiter(self, deli=b"\r\n"):
        """
        找到返回pos，没有返回-1
        """
        return self.stack.find(deli)
    
    def is_empty(self):
        pass


class RequestError(Exception):
    pass

class MethodError(RequestError):
    pass


class Header:

    def __init__(self, conn):
        self._method = None
        self.request = b""
        self.requestline = b""
        self._requestheaders = b""

    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, value):
        if value not in ("GET", "POST", "PUT", "HEAD", "DELETE", "OPTIONS", "CONNECT", "TRACE"):
            raise RequestError("reqeuset method error")

    def getRequest(self):

        for l in iter(partial(conn.recv, 4096), b"\r\n\r\n"):

            if l == b"":
                raise RequestError("peer close connection")

            self.request += l

            if len(self.request) >= 8192:
                raise RequestError("request too long")
    
    def parseHead(self):
        requestline = self.request[:self.request.find(b"\r\n")]

        self.method, path, proto = requestline.split(b" ")
        
