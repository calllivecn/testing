#!/usr/bin/env python3
# coding=utf-8
# date 2020-09-04 11:04:38
# author calllivecn <calllivecn@outlook.com>


import io
import sys
import socket

# 可以避免GC~!~!
# 可是效率没有提升呀。。。。

# 2021-11-10
# 等等，bytearray() 和 io.BytesIO() 有一样的效果？

#BUFVIEW = io.BytesIO(bytes(4096)).getbuffer()
BUFVIEW = bytearray(4096)

def server_bufview():
    sock = socket.socket()
    
    sock.bind(("0.0.0.0", 6788))
    sock.listen(128)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    
    while True:
        client, addr = sock.accept()
        print("remote address:", addr)
    
        while True:
            n = client.recv_into(BUFVIEW)
            if BUFVIEW[:4] == b"quit":
                client.close()
                print("quit")
                break
            elif n == 0:
                print("close()")
                break
    
        #print("接收字节:", n, "前16个字节内容:", BUFVIEW[:16].tobytes())
        print("接收字节:", n, "前16个字节内容:", BUFVIEW[:16])
        print("ok")

    sock.close()


def server(bufsize=4096):
    sock = socket.socket()
    
    sock.bind(("0.0.0.0", 6788))
    sock.listen(128)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    
    while True:
        client, addr = sock.accept()
        print("remote address:", addr)
    
        while b"quit" not in ( n := client.recv(bufsize)):
            pass

        print("quit")
        client.close()
    
        print("接收字节:", n, "前16个字节内容:", n[:16])
        print("ok")

    sock.close()


if __name__ == "__main__":
    if sys.argv[1] == "--server":
        server()
    elif sys.argv[1] == "--server-bufview":
        server_bufview()
    elif sys.argv[1] == "--client":
        client()
    else:
        print("--server | --server-bufview | --client"):
        sys.exit(2)
