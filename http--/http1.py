#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-18 09:56:01
# author calllivecn <c-all@qq.com>

#import ssl
import time
import json
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
        print("HTTP version:", self.request_version)
        print("client IP:", self.client_address)

        self.server_version = "server/0.2 zx/1.0"
        self.sys_version = ""

        # 返回http协议版本
        self.protocol_version = "HTTP/1.1"

        # parse 参数
        pr = parse.urlparse(self.path)
        print(pr)

        # read() body
        body = self.rfile.read(int(self.headers["Content-Length"]))
        print(f"read json data: {json.loads(body)}")

        # process content
        content = "hello, world!".encode()
        content_length = len(content)


        self.send_response(200)

        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", content_length)
        self.end_headers()

        time.sleep(1)

        self.wfile.write(content)

    def do_POST(self):
        self.do_GET()


#httpd = HTTPServer(("127.0.0.1", 6789), Handler)
httpd = ThreadHTTPServer(("127.0.0.1", 6789), Handler)
try:
    httpd.serve_forever()
finally:
    httpd.server_close()
    print("Close server")
