#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-18 09:56:01
# author calllivecn <calllivecn@outlook.com>

import os
#import ssl
import time
import json
import socket
import multiprocessing
from urllib import parse
from socketserver import ThreadingMixIn
from http.server import (
                        HTTPServer,
                        # ThreadingHTTPServer, 3.7 版本新功能。
                        BaseHTTPRequestHandler,
                        SimpleHTTPRequestHandler
                        )

# 手动添加 threading 版本
class ThreadHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        #print("HTTP version:", self.request_version)
        #print("client IP:", self.client_address)

        self.server_version = "server/0.2 zx/1.0"
        self.sys_version = ""

        # 返回http协议版本
        self.protocol_version = "HTTP/1.1"

        # parse 参数
        pr = parse.urlparse(self.path)
        #print(pr)

        # headers
        #print(f"headers: {self.headers}")

        # read() body 没有Content-Length 头，就是没有body
        length = self.headers.get("Content-Length")
        if length is None:
            # length = 0, not body
            body = b""
        else:
            body = self.rfile.read(int(length))
            #print(f"read json data: {json.loads(body)}")


        # process content
        content = "hello, world!".encode()
        content_length = len(content)


        self.send_response(200)

        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", content_length)
        self.end_headers()

        #time.sleep(1)

        self.wfile.write(content)

    def log_message(self, *args):
        pass


def run_multiproces(name):
    addr = ("0.0.0.0", 6782)
    print(f"process: {name} listening: {addr}")

    #httpd = HTTPServer(addr, Handler)

    httpd = ThreadHTTPServer(addr, Handler, bind_and_activate=False)
    httpd.allow_reuse_address = True
    httpd.request_queue_size = 1024

    #httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

    httpd.server_bind()
    httpd.server_activate()


    # 这3个好像没用
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5) # 75 -> 5
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20) # 7200 -> 200
    #httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3) # 9 -> 3

    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        print(f"process: {name} Close server")


proc = []
for i in range(os.cpu_count()):
#for i in range(2):
    mp = multiprocessing.Process(target=run_multiproces, args=(i,), daemon=True)
    mp.start()
    proc.append(mp)


try:
    for mp in proc:
        mp.join()
except Exception:
    print("over done")
