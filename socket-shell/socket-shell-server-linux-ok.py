#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-12 15:44:57
# author calllivecn <c-all@qq.com>

import os
import sys
import pty
# import asyncio
import pickle
import socket
import threading
import selectors
from subprocess import run, Popen, PIPE, STDOUT

#################### 分割线

import os
import sys
import select
import termios
import tty
import pty
from subprocess import Popen


def 这个是网络抄的可以的():
    command = 'bash'
    # command = 'docker run -it --rm centos /bin/bash'.split()
    
    listen_addr = ("0.0.0.0", 6789)
    
    sock = socket.socket()
    sock.bind(listen_addr)
    sock.listen(5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    
    print("listen:", listen_addr)

    while True:
        client, addr = sock.accept()
        print("client connect:", addr)

        # 拿到对端的pty设置, x
        #remote_tty = pickle.loads(client.recv(1024))

        # save original tty setting then set it to raw mode
        #old_tty = termios.tcgetattr(sys.stdin)

        #tty.setraw(sys.stdin.fileno())
        
        # open pseudo-terminal to interact with subprocess
        master_fd, slave_fd = pty.openpty()

        #termios.tcsetattr(master_fd, termios.TCSADRAIN, remote_tty)
        
        # use os.setsid() make it run in a new process group, or bash job control will not be enabled
        p = Popen(command,
                  preexec_fn=os.setsid,
                  stdin=slave_fd,
                  stdout=slave_fd,
                  stderr=slave_fd,
                  universal_newlines=True)
        
        while p.poll() is None:
            #r, w, e = select.select([sys.stdin, master_fd], [], [])
            r, w, e = select.select([client, master_fd], [], [])
            #if sys.stdin in r:
                #d = os.read(sys.stdin.fileno(), 1024)
            if client in r:
                #d = os.read(client.fileno(), 1024)
                d = client.recv(1024)
                print("client read data:", d)
                os.write(master_fd, d)

                """
                if d == b"\x04" or d == b"":
                    print("loop over")
                    break
                """
            elif master_fd in r:
                o = os.read(master_fd, 1024)
                if o:
                    #os.write(sys.stdout.fileno(), o)
                    client.send(o)


        
        # restore tty settings back
        #termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty)
        
        print(addr, "disconnect")
        client.close()

    sock.close()
    exit(0)

#这个是网络抄的可以的()


####################
#
# 分割线
#
########################3333

CMD='bash -i'

def socketshell(sock):
    env = os.environ.copy()
    pty_master, pty_slave = pty.openpty()

    ss = selectors.DefaultSelector()

    ss.register(pty_master, selectors.EVENT_READ)
    ss.register(sock, selectors.EVENT_READ)

    #swap(sock, pty_master)

    #p = Popen(CMD.split(), stdin=sock.fileno(), stdout=sock.fileno(), stderr=STDOUT, env=env)
    p = Popen("bash".split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)

    while p.poll() is None:

        for key, event in ss.select():
            fd = key.fileobj
            if fd == sock:
                data = sock.recv(1024)
                os.write(pty_master, data)

            elif fd == pty_master:
                data = os.read(pty_master, 1024)
                if data:
                    sock.send(data)

        #print("新的一轮 select()")

    print("p.wait()")
    p.wait()
    print("sock.close()")
    sock.close()
    ss.close()
    print("sock exit")


# 使用伪终端的方式
def read(fd, sock):
    data = os.read(fd, 1024)
    sock.send(data)
    return data

def write(fd, sock):
    data = sock.recv(1024)
    os.write(fd, data)
    return data

# 使用伪终端的方式
def socketpty(sock):
    pty.spawn("bash", lambda fd: read(fd, sock))

def server():
    listen_addr = ("0.0.0.0", 6789)
    sock = socket.socket()
    sock.bind(listen_addr)
    sock.listen(5)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    print(sys.argv[0], "start:", listen_addr)

    while True:
        client, addr = sock.accept()
        print("client", addr)

        th = threading.Thread(target=socketshell, args=(client,), daemon=True)

        # 验证使用pty
        #th = threading.Thread(target=socketpty, args=(client,))

        th.start()

server()
exit(0)
