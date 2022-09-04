#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-02 06:40:01
# author calllivecn <c-all@qq.com>


import threading

from lib1 import server


def tp(name):
    #print("name:", name, server.get())
    print("name:", name)

class Tp(threading.Thread):

    def __init__(self, name):
        super().__init__()
        self.tp_name = name

    def run(self):
        tp(self.tp_name)

# 注册
def onload(s):
    server.set(s)

onload("zx test context variable")

#th = threading.Thread(target=tp)
th = Tp("哈哈")
th.start()

th.join()

print("done")

