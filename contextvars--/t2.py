#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-02 06:40:01
# author calllivecn <c-all@qq.com>



from lib1 import server



def tp():
    print(server.get())


# 注册
def onload(s):
    server.set(s)


onload("zx test context variable")

tp()

