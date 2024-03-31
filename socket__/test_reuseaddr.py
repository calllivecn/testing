#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-23 14:34:39
# author calllivecn <calllivecn@outlook.com>


"""
结论:

1. REUSEPORT 能让多个进程，同时使用一个 (addr , port)
2. 服务器端，一般会加上REUSEADDR选项。

"""

import os
import socket
import multiprocessing as mp 
from threading import Thread

ADDR=("127.0.0.1", 6789)

def server(procname):
    print(f"我是进程: {procname}")

    sock = socket.socket()

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

    sock.bind(ADDR)

    sock.listen(128)

    while True:

        client, addr = sock.accept()

        print(f"我是进程： {procname} 接收到： {addr} 的连接")

        client.close()



procs = []
for i in range(os.cpu_count()):
    th = mp.Process(target=server, args=(f"{i} 号",))
    th.start()
    procs.append(th)



for p in procs:
    p.join()
