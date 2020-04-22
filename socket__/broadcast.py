#!/usr/bin/env python3
# coding=utf-8
# date 2020-04-22 09:09:54
# author calllivecn <c-all@qq.com>

"""
记录一些坑：

1. 只需要发送广播的设置sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
2. client 和 server  都bind（）一下地址。方便防火墙设置通过。
"""


import sys
import socket
import readline


BIND_ADDR = ("", 6789)
BROADCAST_ADDR = ("<broadcast>", 6789)

def client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(BIND_ADDR)
    sock.settimeout(3)

    while True:
        in_ = input("enter: ")
        sock.sendto(in_.encode(), BROADCAST_ADDR)

        if "quit" == in_:
            break

        try:
            data, addr = sock.recvfrom(256)
        except socket.timeout:
            print("recv timeout.")
            continue

        print(f"{addr} -- recv: {data.decode()}")

    sock.close()

def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    sock.bind(BIND_ADDR)

    while True:
        data, addr = sock.recvfrom(256)
        print(f"client: {addr}")

        if b"quit" == data[:4]:
            print("quit")
            break
        sock.sendto(b"ok", addr)

    sock.close()



if "client" == sys.argv[1]:
    client()
elif "server" == sys.argv[1]:
    server()