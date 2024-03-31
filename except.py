#!/usr/bin/env python3
# coding=utf-8
# date 2019-07-30 17:02:07
# author calllivecn <calllivecn@outlook.com>

import time

import random

i = 0 
while True:
    i += 1

    try:
        time.sleep(1)
        print(i, "-"*10, "分割线", "-"*10)

        tf = random.choice((True, False))

        if tf:
            print("正常执行")
        else:
            print("抛出异常")
            raise Exception("。。。")

    except Exception:
        print("except --> continue")
        continue

    finally:
        print("finally -- > ")

