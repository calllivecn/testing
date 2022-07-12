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
import traceback
import subprocess
from pathlib import Path
from threading import Thread


from common import (
    PacketError,
    PacketType,
    Transport,
    get_server_cfg,
    get_client_cfg,
)





def run(transport, cmd, cwd=None):
    # 如果你希望捕获并将两个流合并在一起，使用 stdout=PIPE 和 stderr=STDOUT 来代替 capture_output。
    with subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cwd, encoding="utf8", universal_newlines=True, bufsize=1) as p:
        # py3.6
        while True:
            data = p.stdout.readline()
            if data != "":
                transport.write(PacketType.CMD_OUTPUT, data.encode("utf8"))
            else:
                break
            # log 
            sys.stdout.write(data)

    # 发送退出码
    transport.write(PacketType.RECODE, p.returncode.to_bytes(2, "big"))


def cmd_thread(conn, s_secret):
    try:
        V = Transport(conn)

        V.recv_verify_request()

        c_secret, cmd, cwd = get_client_cfg(V.id_client)

        # 验证client ok
        if V.server(c_secret):
            ptype, payload = V.read()
            if ptype != PacketType.CMD_ARGS:
                raise PacketError("CMD Error")

            cmd_args = payload.decode("utf8")
            print(f"cmd: {cmd}, cmd_args: {cmd_args}")
            cmd = " ".join([str(Path(cmd)), cmd_args])
            run(V, cmd, cwd)
        else:
            print(f"verify client error")
    except Exception:
        traceback.print_exc()
    
    finally:
        V.close()


def server():

    s_secret, host, port = get_server_cfg()
    print(s_secret, host, port)

    with socket.create_server((host, int(port)), family=socket.AF_INET6, backlog=128) as sock:
        while True:
            conn, addr = sock.accept()
            print(f"{addr} connected.")
            th = Thread(target=cmd_thread, args=(conn, s_secret))
            th.start()




if __name__ == "__main__":
    # print(run("bash -c 'echo line1;echo lin2;echo line3;'"))
    server()
