#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-19 14:31:24
# author calllivecn <c-all@qq.com>


import os
import socket
import selectors
import threading
from http import HTTPStatus
from functools import partial


class Request:

    def __init__(self, sock):
        """
        暂定，在这里处理请求头。
        """
        self.client = sock

        self.headers = {}
    
    def parse_cmd_line(self):
        words = self._readline()
        if len(words) > 65535:
            self._request_error(HTTPStatus.REQUEST_URI_TOO_LONG, "bad request")
            return

        if len(words) != 3:
            self._request_error(HTTPStatus.BAD_REQUEST, "bad request")
            return
        
        cmd, path, protocol = words.decode("utf8").split(" ")

        version_number = protocol.split("/")
        if version_number != (1, 1):
            self._request_error(HTTPStatus.BAD_REQUEST, "Unsupported version")
            return

    def parse_headers(self):
        for header in iter(partial(self._readline), ""):
            head, value = header.split(":")
            self.headers[head.split()] = value.split()

    def _request_error(self, recode, msg):
        b = " ".join([str(recode), msg]).encode("utf8")
        self.client.send(b)
        self.client.shutdown(socket.SHUT_RDWR)
        self.client.close()
        return


    def _readline(self):
        head = ""
        CRLF = b"\r\n"
        LF = b"\n"
        while True:

            d = self.client.recv(1)

            if not d:
                break

            if d == LF:
               head += LF 
            else:
                head += d
                
        return head.rstrip(b"\r\n")


class HTTPServer:
    """

    """

    def __init__(self, bind_addr):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.server_sock.setblocking(False)

        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        
        self._selector = selectors.DefaultSelector()
        self._selector.register(self.server_sock, selectors.EVENT_READ)


    def handle():
        pass

    def run(self):
        for event, key in self._selector.select():
            key.fileobj.accept()

    def get_request(self):
        client = self.server_sock.accept()
        return Request(client)
        
    