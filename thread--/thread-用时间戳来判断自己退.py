#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-23 04:09:14
# author calllivecn <c-all@qq.com>


import time
import threading

"""
2023-08-08
这个需求应该使用threading.Event() 来实现更合适
"""


def newthread(func):

    def wrap(*args, **kwargs):

        print("线程启动")
        th = threading.Thread(target=func, args=args, kwargs=kwargs)
        th.start()
        return th

    return wrap


class Run:


    def __init__(self):
        self.run_id = 0


    def start(self):
        self.run_id = time.monotonic()
        print(f"Run ID: {self.run_id}")

        self.run(self.run_id)

    @newthread
    def run(self, run_id):

        print(f"我的 run_id: {run_id}")

        while True:
            if self.run_id != run_id:
                print(f"run_id: {run_id} exit")
                break
            else:
                print("I'm is alive")
                time.sleep(1)





run = Run()

run.start()

time.sleep(5)

run.start()

