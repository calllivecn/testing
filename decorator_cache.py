#!/usr/bin/env python3
# coding=utf-8
# date 2020-11-28 15:00:00
# author calllivecn <calllivecn@outlook.com>



"""
记一次，在线coding面试。

题目：
    请用python实现cache功能： 若在n秒内使用相同的keywords调用query函数查询，则直接返回query函数上一次返回的内容，
    需要自己构造出命中或者不命中cache以及超时场景，执行结果，分别打印出请求是否使用缓存以及缓存超时的情况。
"""

import time

d = {}

def cache(arg_n):

    def func(func):

        lasttime = time.time()

        def warp(*args, **kwargs):

            nonlocal lasttime
            global d

            # result = func(*args, **kwargs)

            if d.get(args[0]) == None:
                # 没有命中
                print("没命中")
                result = func(args[0])
                d[args[0]] = result
                return result
            else:
                # 命中
                nowtime = time.time()

                if (nowtime - lasttime) <= arg_n:
                    print("命中")
                    lasttime = nowtime
                    return d[args[0]]
                else:
                    print("超时, 重新请求")
                    result = func(*args, **kwargs)
                    d[args[0]] = result
                    return result

        return warp
    
    return func


data = {"1": 1, "2": 2, "3": 3}

@cache(3)
def get_news(key):
    return data.get(key)

print(get_news("1"))
print(get_news("2"))
print(get_news("2"))
time.sleep(1)
print(get_news("2"))
print(get_news("2"))

time.sleep(4)

print(get_news("1"))
