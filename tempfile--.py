#!/usr/bin/env python3
# coding=utf-8
# date 2020-06-09 14:39:24
# author calllivecn <c-all@qq.com>

import os
import tempfile

def nametempfile(context):

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(context)
        print("创建临时文件:", f.name)
        return f.name


fname = nametempfile("这是临时文件".encode())
input("wait... [enter continue]")
os.remove(fname)
