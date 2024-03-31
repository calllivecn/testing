#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-24 02:13:30
# author calllivecn <calllivecn@outlook.com>


"""
1. 手动测试小包，是一发一收对应的。
2. 慢速发送 测试随机大包， 500~48K 的随机数据包测试，没问题。
3. 快速发送 测试随机大包， 1K~62K 的随机数据包测试，有问题。
    (1) 接收速度慢的会直接丢掉，来不急处理的包。
    (2) 还是会接收到很少的埙坏数据包。why???
"""

import os
import sys
import time
import binascii
import hashlib
import socket
import random

MIN_BLOCK = 1024
recv_buf = 48 * (1<<10)
BLOCK = recv_buf - 32 - 20 
# 48K, 32byte 是校验头， 20byte UDP头???
# 尝试解决 OSError: [WinError 10040]

def sha256(msg):
    sha = hashlib.sha256(msg)
    return sha.digest()


def rand_data():
    length = random.randint(MIN_BLOCK, BLOCK)
    #length = 1024
    data = os.urandom(length)
    sha = sha256(data)

    return sha + data


def server(port=8777):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind(("0.0.0.0", port))

    while True:
        try:
            data, addr = sock.recvfrom(recv_buf)
        except OSError:
            print('''OSError: [WinError 10040] 一个在数据报套接字上发送的消息大于内部消息缓冲区或其他 一些网络限制，或该用户用于接收数据报的缓冲区比数据报小''')
            print(f"data length: {len(data)}")
            sys.exit(2)

        before_sha = data[:32]
        #print(f"sha256 length: {len(before_sha)}")
        after_sha = sha256(data[32:])

        if before_sha == after_sha:
            print(f"recv length: {len(data)} 源sha256 等于 接收到的sha256")
        else:
            print(f"recv length: {len(data)} 源sha256 不等于 接收到的sha256")
            print(f"源sha256: {binascii.b2a_hex(before_sha)}\n现sha256: {binascii.b2a_hex(after_sha)}")

        #sock.sendmsg(b"ok")


def client(addr, port=8777):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    while True:


        # 慢速发送测试
        #data = input(">>> ")
        #if data == "quit":
        #    print("exit.")
        #    break

        # 改为 快速发送测试 
        data = rand_data()
        # 慢一点点
        #time.sleep(0.01)

        sha = sha256(data)

        #print(f"sha256 byte length: {len(sha)}")

        data = sha + data

        print(f"recv length: {len(data)} 源sha256: {binascii.b2a_hex(sha)}")
        sock.sendto(data, (addr, port))



if __name__ == "__main__":

    try:
        a = sys.argv[1]
    except Exception:
        print(f"用法： {sys.argv[0]} <--server> [port  = 8777]")
        print(f"用法： {sys.argv[0]} <--client> <address> [port = 8777]")
        sys.exit(1)


    if sys.argv[1] == "--server":
        try:
            port = int(sys.argv[2])
        except Exception:
            port = 8777
        server(port)
    elif sys.argv[1] == "--client":
        try:
            port = int(sys.argv[3])
        except Exception:
            port = 8777

        client(sys.argv[2], port)
    else:
        print(f"用法： {sys.argv[0]} <--server> [port  = 8777]")
        print(f"用法： {sys.argv[0]} <--client> <address> [port = 8777]")
