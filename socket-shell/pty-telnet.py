#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-13 11:34:35
# author calllivecn <c-all@qq.com>


import os
import sys
import tty
import fcntl
import struct
import signal
import socket
import termios
import selectors

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


def client(addr, port):
    server_addr = (addr, port)

    signal.signal(signal.SIGWINCH, signal_SIGWINCH_handle)
    

    sock = socket.create_connection(server_addr)

    # tty 
    tty_bak = termios.tcgetattr(STDIN)
    tty.setraw(STDIN)


    ss = selectors.DefaultSelector()

    ss.register(sock, selectors.EVENT_READ)
    ss.register(STDIN, selectors.EVENT_READ)

    RUNNING = True
    while RUNNING:
        for key, event in ss.select():
            fd = key.fileobj
            if fd == sock:
                data = sock.recv(1024)
                if not data:
                    RUNNING = False
                    break
                os.write(STDOUT, data)
            elif fd == STDIN:
                data = os.read(STDIN, 1024)
                sock.send(data)

    ss.close()

    termios.tcsetattr(STDIN, termios.TCSADRAIN, tty_bak)


if __name__ == "__main__":
    client(sys.argv[1], int(sys.argv[2]))
