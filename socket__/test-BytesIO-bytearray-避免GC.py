#!/usr/bin/env python3
# coding=utf-8
# date 2020-09-04 11:04:38
# author calllivecn <c-all@qq.com>


import io
import socket

# 可以避免GC~!~!

#BUFVIEW = io.BytesIO(bytes(4096)).getbuffer()
BUFVIEW = bytearray(4096)

sock = socket.socket()

sock.bind(("0.0.0.0", 6788))
sock.listen(128)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

while True:
    client, addr = sock.accept()
    print("remote address:", addr)

    while True:
        n = client.recv_into(BUFVIEW)
        if BUFVIEW[:len(b"quit")] == b"quit":
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
