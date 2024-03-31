#!/usr/bin/env python3
# coding=utf-8
# date 2019-12-19 22:58:16
# author calllivecn <calllivecn@outlook.com>

import sys
import time
import signal


def timer(sig, frame):
    print("计时时间到：", t)
    print(type(sig), "--", sig)
    print(type(frame), "--", frame)
    print("收到：", sig, "信号")
    print("退出程序")
    sys.exit(0)


t = 3
signal.alarm(t)

signal.signal(signal.SIGALRM, timer)

print("main() sleep ... 5s")
time.sleep(5)
