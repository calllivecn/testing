#!/usr/bin/env python3
# coding=utf-8
# date 2021-06-27 21:48:14
# author calllivecn <c-all@qq.com>


import time
import threading
from multiprocessing import Pipe



def send(pipe):
    i=0
    while True:
        pipe.send_bytes(b"-"*i)
        i+=1
        time.sleep(0.5)


def recv(pipe):
    while True:
        print(pipe.recv_bytes(8))


s, r = Pipe()

th = threading.Thread(target=recv, args=(r,))
th.start()

send(s)
