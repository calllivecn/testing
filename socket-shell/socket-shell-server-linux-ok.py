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
from multiprocessing import Process


SHELL='bash'

# 管理子进程退出的
class Watch(threading.Thread):

    def __init__(self, pty_slave):
        super().__init__()

        self.rpipe, self.wpipe = os.pipe()
        self.pty_slave = pty_slave
    
    def run(self):
        self.p = Popen(SHELL.split(), stdin=self.pty_slave, stdout=self.pty_slave, stderr=self.pty_slave, preexec_fn=os.setsid, universal_newlines=True)
        recode = self.p.wait()
        os.write(self.wpipe, recode.to_bytes(4, "big"))

    def recode(self):
        I = os.read(self.rpipe, 4)
        return int.from_bytes(I, "big")


    def fileno(self):
        return self.rpipe

    def close(self):
        os.close(self.rpipe)
        os.close(self.wpipe)


def socketshell(sock):
    try:
        env = os.environ.copy()
        pty_master, pty_slave = pty.openpty()

        ss = selectors.DefaultSelector()

        ss.register(pty_master, selectors.EVENT_READ)
        ss.register(sock, selectors.EVENT_READ)

        # p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)

        p = Watch(pty_slave)
        p.start()
        p_fd = p.fileno()

        ss.register(p_fd, selectors.EVENT_READ)

        # while p.poll() is None:
        RUNNING=True
        while RUNNING:
            for key, event in ss.select():
                fd = key.fileobj
                if fd == sock:
                    data = sock.recv(1024)
                    
                    # 在peer挂掉的情况下会出现
                    if data == b"":
                        p.communicate()
                        RUNNING = False
                        break
                    os.write(pty_master, data)

                elif fd == pty_master:
                    data = os.read(pty_master, 1024)
                    if data:
                        sock.send(data)

                elif fd == p_fd:
                    recode = p.recode()
                    print("shell exit code:", recode)
                    RUNNING = False
                    break

    except Exception as e:
        print(f"捕获到异常退出: {e}")

    finally:
        print(f"client disconnected: {sock.getsockname()}")
        sock.close()
        ss.close()
        p.close()
        os.close(pty_master)
        os.close(pty_slave)


def server():
    listen_addr = ("", 6788)
    sock = socket.create_server(listen_addr, family=socket.AF_INET6, reuse_port=True)

    print(sys.argv[0], "start:", listen_addr)

    while True:
        client, addr = sock.accept()
        print("client", addr)

        # th = threading.Thread(target=socketshell, args=(client,))
        # 使用进程
        th = Process(target=socketshell, args=(client,))
        th.start()
        client.close()
server()
