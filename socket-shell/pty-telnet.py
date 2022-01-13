#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-13 11:34:35
# author calllivecn <c-all@qq.com>


import os
import sys
import tty
import socket
import termios
import selectors


addr = (sys.argv[1], int(sys.argv[2]))

sock = socket.socket()

sock.connect(addr)

# tty 
tty_bak = termios.tcgetattr(sys.stdin)
tty.setraw(sys.stdin.fileno())

STDIN = sys.stdin.fileno()
STDOUT = sys.stdout.fileno()

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

