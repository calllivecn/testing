#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-04 11:08:03
# author calllivecn <calllivecn@outlook.com>

import queue

import threading 

import multiprocessing as mp

# 这俩不一样，这个有 q.close()
# q = mp.Queue(4)
q = queue.Queue(4)

def thread1(q):
    while (task :=q.get()) is not None:
        print("thread get()", task)

    print("exit")



th = threading.Thread(target=thread1, args=(q,))
th.start()


while True:
    data = input("Enter:")
    print()
    if data == ".exit":
        if isinstance(q, queue.Queue):
            q.put(None)
        elif isinstance(q, mp.Queue):
            q.close()
        break
    else:
        q.put(data)

