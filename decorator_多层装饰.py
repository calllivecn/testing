#!/usr/bin/env python3
# coding=utf-8
# date 2020-11-28 17:43:37
# author calllivecn <c-all@qq.com>

import time


def runningtime(func):

    def warp(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f"{func.__name__} 的运行时间: {t2-t1} /秒")
        return result

    return warp



def pack(func):

    def warp(*args, **kwargs):

        print("运行函数前...")
        result = func(*args, **kwargs)
        print("运行函数后...")
        return result

    return warp



@runningtime
@pack
def p():
    print("这是一个被装饰的函数")


p()
