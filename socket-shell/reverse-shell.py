#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-12 15:44:57
# author calllivecn <c-all@qq.com>

import os
import sys
import pty
import socket
import threading
import selectors
from subprocess import Popen

SHELL='bash -i'

def socketshell(sock):
    try:
        env = os.environ.copy()
        pty_master, pty_slave = pty.openpty()

        ss = selectors.DefaultSelector()

        ss.register(pty_master, selectors.EVENT_READ)
        ss.register(sock, selectors.EVENT_READ)

        p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)

        while p.poll() is None:

            for key, event in ss.select():
                fd = key.fileobj
                if fd == sock:
                    data = sock.recv(1024)
                    print("recv:", data)
                    
                    # 在peer挂掉的情况下会出现
                    if data == b"":
                        p.communicate()
                        break
                    os.write(pty_master, data)

                elif fd == pty_master:
                    data = os.read(pty_master, 1024)
                    if data:
                        sock.send(data)

            #print("新的一轮 select()")
    except Exception as e:
        # raise e
        print(f"捕获到异常退出: {e}")

    finally:
        sock.close()
        ss.close()
        print("sock exit")

def server():
    listen_addr = ("0.0.0.0", 6788)
    sock = socket.socket()
    sock.bind(listen_addr)
    sock.listen(5)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    print(sys.argv[0], "start:", listen_addr)

    while True:
        client, addr = sock.accept()
        print("client", addr)

        th = threading.Thread(target=socketshell, args=(client,), daemon=True)
        th.start()

server()
