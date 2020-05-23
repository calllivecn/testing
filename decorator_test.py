#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-21 11:22:52
# author calllivecn <c-all@qq.com>

import time

def test(func):
    def wrapper(*args,**kw):
        print('func 执行前.')
        func(*args,**kw)
        print('func 执行后.')
    return wrapper


@test
def tmp(text):
    print('this tmp function() -->',text)


tmp('execute1')


def text(prompt):

    def decorator(func):

        def warp(*arg, **kwarg):
            print(prompt)
            result = func(*arg, **kwarg)
            print(prompt)
            return result

        return warp

    return decorator



@text("3")
@text("2")
@text("1")
def test_func():
    print("当前时间:",time.localtime())


test_func()
