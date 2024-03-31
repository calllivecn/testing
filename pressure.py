#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-09 14:38:54
# author calllivecn <calllivecn@outlook.com>

"""
PSI 阈值监控
用户可以向 PSI 注册触发器，在资源压力超过自定义的阈值时获得通知。
一个触发器定义了特定时间窗口内最大累积停顿时间，
例如，在任何 500ms 的窗口内，累计 100ms 的停顿时间会产生一个通知事件。

如何向 PSI 注册触发器呢？
打开 /proc/pressure/ 目录下资源对应的 PSI 接口文件，写入想要的阈值和时间窗口，
然后在打开的文件描述符上使用 select()、poll() 或 epoll() 方法等待通知事件。
写入 PSI 接口文件的数据格式为: <some|full> <停顿阈值> <时间窗口>
举个例子，向 /proc/pressure/io 写入 "some 500000 1000000"，代表着在任何 1 秒的时间窗口内，
如果一个或多个进程因为等待 IO 而造成的时间停顿超过了阈值 500ms，将触发通知事件。
当用于定义触发器的 PSI 接口文件描述符被关闭时，触发器将被取消注册。
"""

import time

def read(p="/proc/pressure/cpu"):
	with open(p) as f:
		return f.read()


def main():

	while True:
		print("CPU: ", read())
		print("IO: ", read("/proc/pressure/io"))
		print("MEMORY: ", read("/proc/pressure/memory"))
		time.sleep(1)


if __name__ == "__main__":
	main()