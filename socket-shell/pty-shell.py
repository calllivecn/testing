#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-13 05:57:26
# author calllivecn <c-all@qq.com>

import os
import io
import sys
import time

def child(master, slave):
    os.close(master)
    os.dup2(slave, 0)
    os.dup2(slave, 1)
    os.dup2(slave, 2)

    os.execvp("/bin/bash", ["bash", "-l", "-i"])


def parent():
    master, slave = os.openpty()
    new_pid = os.fork()
    if new_pid == 0:
        child(master, slave)

    time.sleep(1)

    os.close(slave)

    os.write(master, b"fg\n")
    time.sleep(1)
    _ = os.read(master, 1024)

    data = sys.argv[1] + "\n"
    os.write(master, data.encode("utf-8"))
    time.sleep(1)

    lines = io.BytesIO()
    
    fd = sys.stdout.fileno()

    while True:
        tmp = os.read(master, 1024)
        #lines.write(tmp)
        os.write(fd, tmp)
        if len(tmp) < 1024:
            break

    #print(lines.getvalue())

parent()
