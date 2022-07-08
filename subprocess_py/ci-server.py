#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-06 16:24:53
# author calllivecn <c-all@qq.com>

"""
0. 使用sha256(client_id + secret + timestamp)进行身份验证
1. 使用 socket 把命令的输出和退出码发送到 client 端(CI)。
"""


import sys
import socket
import shlex
import subprocess
from threading import Thread

from common import (
    PacketError,
    Verify,
    Transport,
)


def run(conn, id_, cmd, cwd=None):
    transport = Transport(conn)
    # 如果你希望捕获并将两个流合并在一起，使用 stdout=PIPE 和 stderr=STDOUT 来代替 capture_output。
    # p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, universal_newlines=True)
    p = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, universal_newlines=True, bufsize=1)

    while (data := p.stdout.readline()) != "":
        transport.write(data.encode("utf8"))

        # client 使用以下，输出。
        # sys.stdout.write(f"{i}: {data}")

    # 发送退出码
    transport.recode(p.returncode)


def cmd_thread(conn):

    V = Verify(conn, s_secret)
    if V.client():
        # 
        rcmd(conn, id_, cmd, cwd)
    else:
        print("")



def server(host, port=17787):

    with socket.create_server((host, port), family=socket.AF_INET6, backlog=128) as sock:
        while True:
            conn, addr = sock.accept()

            th = Thread(target=cmd_thread, args=(conn,))
            th.start()




if __name__ == "__main__":
    # print(run("bash -c 'echo line1;echo lin2;echo line3;'"))
    print(run("ping 223.5.5.5"))