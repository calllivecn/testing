#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-08 17:26:17
# author calllivecn <c-all@qq.com>


import os
import sys
import socket
from tkinter import Pack

from common import (
    PacketError,
    PacketType,
    Transport,
)

"""
app = os.environ.get("app")
username = os.environ.get("username")
config = os.environ["config.txt"]
"""

id_ = os.environ["id_client"]
c_secret = os.environ["c_secret"]
s_secret = os.environ["s_secret"]

HOST="9.86.198.91"
HOST="::1"
PORT=17787

def test():
    conn = socket.create_connection((HOST, PORT), timeout=30)

    # verify
    V = Transport(conn)
    if not V.client(int(id_), c_secret, c_secret):
        print(f"verify server error")
        sys.exit(1)

    cmd_args = f"-t -asldkjfief -l 128 223.5.5.5"
    cmd_args = f"-lh"
    # 发送命令的参数
    V.write(PacketType.CMD_ARGS, cmd_args.encode("utf8"))

    # py3.6
    while True:
        ptype, payload = V.read()

        if ptype == PacketType.CMD_OUTPUT:
            sys.stdout.write(payload.decode("utf8"))
        
        elif ptype == PacketType.RECODE:
            print("cmd recode: ", int.from_bytes(payload, "big"))
            break
        else:
            raise PacketError("unknown packet type")


if __name__ == "__main__":
    test()

