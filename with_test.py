#!/usr/bin/env python3
#coding=utf-8


import sys

class zx:
    def __init__(self):
        print("__init__()")

    def __enter__(self):
        print("with 打开")
        return 4

    def __exit__(self, exec_type, exec_value, exec_tb):
        print(exec_type, exec_value, exec_tb)
        print('with关闭')


with zx() as z:
    print(z)

