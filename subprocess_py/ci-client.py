#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-08 17:26:17
# author calllivecn <c-all@qq.com>


import os
import socket

# from libprotocmd import

app = os.environ.get("app")
username = os.environ.get("username")
config = os.environ["config.txt"]

HOST="9.86.198.91"
PORT=19989

def test():
    sock = socket.create_connection((HOST, PORT), timeout=30)

    # verify
    client_verify(sock

    # py3.6
    while True:
        stdout = sock.read(1024)

    sock.close()


if __name__ == "__main__":
    test()

