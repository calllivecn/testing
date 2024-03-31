#!/usr/bin/env python3
# coding=utf-8
# date 2020-10-19 14:31:24
# author calllivecn <calllivecn@outlook.com>


import os
import socket
import threading
from http import HTTPStatus
from functools import partial


class Request:

    def __init__(self, sock, client_addr):
        """
        暂定，在这里处理请求头。
        """
        self.client = sock
        self.client_addr = client_addr

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

    def __init__(self, server_addr, bind_addr=True):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #self.server_sock.setblocking(False)

        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        
        if bind_addr:
            self.serve_bind_accept(server_addr)

    def handle(self, client_sock, addr):
        req = Request(client_sock) 
        req.

    def serve_bind_accept(self, address=("", 8080), listen=128):
        self.server_sock.bind(address)
        self.server_sock.listen(listen)

    def run(self):
        while True:
            addr, client = self.server_sock.accept()
            th = threading.Thread(target=self.handle, args=(client, addr))
            th.start()
