#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-30 14:56:21
# author calllivecn <c-all@qq.com>



def coro1():
    word = yield 'hello'

    yield word

    return word


def coro2():
    result = yield from coro1()

    print("coro2 result", result)



def main():
    c2 = coro2()
 
    print(1)
    print(next(c2))

    print(2)
    print(c2.send("world"))

    try:
        print(3)
        c2.send(None)
    except StopIteration:
        pass


main()


