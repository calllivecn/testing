#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-09 00:15:20
# author calllivecn <calllivecn@outlook.com>



import queue
from threading import Thread

s_put = queue.Queue(5)

s_get = queue.Queue(5)


def puter():
    for i in range(10):
        print("s_put({})".format(i))
        s_put.put(i)
        print("blocking...")
        s_put.join()
        print("s_put done")
        print("entry continue: ")
        input()



th = Thread(target=puter,daemon=True)
th.start()

while True:
    i = s_put.get()
    print("s_put.get({})".format(i))
    s_put.task_done()
    print("s_put.task_done()")

