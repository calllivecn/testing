#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-18 09:56:01
# author calllivecn <calllivecn@outlook.com>

#import ssl
import time
import json
from urllib import parse
import socket
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

    def log_message(self, *args):
        pass


class Handler(BaseHTTPRequestHandler):

    def send_error(self, code, message=None, explain=None):
        msg = f"{code} {message}"
        self.wfile.write(msg.encode("utf-8"))

    def setup(self):
        super().setup()

        #self.error_message_format=""

        self.server_version = "nginx"
        self.sys_version = ""

        # 返回http协议版本
        self.protocol_version = "HTTP/1.1"

        self.default_request_version = "HTTP/1.1"
    

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        #print("HTTP version:", self.request_version)
        #print("client IP:", self.client_address)

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
        content = "hello, world!\n".encode("utf-8")
        content_length = len(content)


        self.send_response(200)

        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", content_length)
        self.end_headers()

        #time.sleep(1)

        self.wfile.write(content)

    def log_message(self, *args):
        pass

addr = ("0.0.0.0", 6783)
print(f"listening: {addr}")
#httpd = HTTPServer(addr, Handler)
httpd = ThreadHTTPServer(addr, Handler, bind_and_activate=False)
httpd.allow_reuse_address = True
httpd.request_queue_size = 1024

httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5) # 75 -> 5
httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 20) # 7200 -> 200
httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3) # 9 -> 3

httpd.server_bind()
httpd.server_activate()

try:
    httpd.serve_forever()
finally:
    httpd.server_close()
    print("Close server")
