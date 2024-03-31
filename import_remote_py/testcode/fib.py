#!/usr/bin/env python3
#coding=utf-8
# date 2018-03-06 02:28:26
# author calllivecn <calllivecn@outlook.com>

print("I'm fib")

def fib(n):
    if n < 2:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)
