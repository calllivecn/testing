#!/usr/bin/env python3
# coding=utf-8
# date 2020-01-07 16:04:42
# author calllivecn <c-all@qq.com>

import sys
import ssl
import socket
from urllib.parse import urlparse


socket.setdefaulttimeout(5)

headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36"
        }


def check_http2(domainname, port=443):

    try:
        #HOST = urlparse(domainname).netloc
        #PORT = 443

        ctx = ssl.create_default_context()
        ctx.set_alpn_protocols(["h2", "spdy/3", "http/1.1"])

        conn = ctx.wrap_socket(socket.socket(), server_hostname=domainname)

        conn.connect((domainname, port))

        protocol = conn.selected_alpn_protocol()

        if protocol == "h2":
            return {"http2": True}
        else:
            return {"http2": False}

    except Exception as e:
        print("check exception:", e)


if __name__ == "__main__":

    try:
        domain = sys.argv[1] 
    except Exception:
        domain = "www.tmall.com"
    
    try:
        port = int(sys.argv[2])
    except Exception:
        port = 443
    
    try:
        result = check_http2(domain, port)
    except Exception as e:
        print("check_http2 Error:", e)
        sys.exit(0)

    print(domain, ":", result)

