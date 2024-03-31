#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-20 01:45:05
# author calllivecn <calllivecn@outlook.com>


import os
import time
import multiprocessing as mp


def sleep(t):
    time.sleep(t)


def child2child():
    childs = []
    for t in range(4):
    
        p = mp.Process(target=sleep, args=(t*10,))
        p.start()
        childs.append(p)
        print(f"ppid: {mp.parent_process().pid} pid: {p.pid}")


def child():
    p = mp.Process(target=child2child)
    p.start()
    return p


task = child()
print("child:", task)

print("拿到当前进程的所有子进程。")
ps = mp.active_children()
print(f"pids: {ps}")

print(f"这是当前进程: {os.getpid()}")

time.sleep(3)

for p in ps:
    print("kill:", p)
    p.kill()


print("但是需要主进程 是存活的。")