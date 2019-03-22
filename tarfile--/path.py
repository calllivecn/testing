#!/usr/bin/env python3
# coding=utf-8
# date 2019-03-21 12:50:13
# https://github.com/calllivecn


import os
import sys
from os import path


def safe_path(filename):
    realpath = path.realpath(filename)
    member_path = path.split(realpath)
    dirname = path.dirname(realpath)

    print("-"*60)
    print("realpath: ", realpath)
    print("member_path: ", member_path)
    print("dirname: ", dirname)



for fn in sys.argv[1:]:
    safe_path(fn)
