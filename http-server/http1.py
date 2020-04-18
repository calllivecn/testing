#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-18 09:56:01
# author calllivecn <c-all@qq.com>

#import ssl
from urllib import parse
from http.server import (
                        HTTPServer,
                        ThreadingHTTPServer,
                        BaseHttpRequestHandler,
                        SimpleHttpRequestHandler
                        )


class Handler(SimpleHttpRequestHandler):

    def do_GET(self):
        self.send_header("Content", "application/json")
        self.send_response(200, 
