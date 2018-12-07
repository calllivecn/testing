#!/usr/bin/env py3
#coding=utf-8
# date 2018-12-04 11:08:03
# author calllivecn <c-all@qq.com>


import threading 

import multiprocessing as mp

queue = mp.Queue()


def thread1(q):
    while True:

        if q.empty():
            break

        print(q.get())



th = threading.Thread(target=thread1, args=(queue,))
th.start()


while True:
    data = input("Enter:")
    queue.put(data)

