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
    
    def parse_cmd_line(self):
        words = self.fd.readline(65535)
        if len(words) > 65535:
            self.http_error(HTTPStatus.REQUEST_URI_TOO_LONG, "bad request")

        if len(words) != 3:
            self.http_error(HTTPStatus.BAD_REQUEST, "bad request")


    def send_http_error(self, recode, msg):
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

            if d == b"\n" or d == "\r":
                
        return



class HTTPServer:
    """

    """

    def __init__(self, bind_addr, reuseaddr=True):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

        if reuseaddr:
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, reuseaddr)
            self.server_sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
        
        self._selector = selectors.DefaultSelector()
        self._selector.register(self.server_sock, selectors.EVENT_READ, self.get_request)

    def handle():
        pass


    def run(self):
        for event, key in self._selector.select():

    def get_request(self):
        client = self.server_sock.accpet()
        return Request(client)
        
    