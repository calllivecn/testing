#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-06 08:35:04
# author calllivecn <calllivecn@outlook.com>

# 方法一：使用全局变量的列表，来保存返回值


# 方法二：重写 Thread 的 join 方法，返回线程函数的返回值
# 默认的 thread.join() 方法只是等待线程函数结束，没有返回值，我们可以在此处返回函数的运行结果，代码如下：

from threading import Thread


def foo(arg):
    return arg


class ThreadWithReturnValue(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return


twrv = ThreadWithReturnValue(target=foo, args=("hello world",))
twrv.start()
print(twrv.join()) # 此处会打印 hello world。


# 方法三：使用标准库 concurrent.futures

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)


def foo(bar):
    return bar

with ThreadPoolExecutor(max_workers=10) as executor:
    to_do = []
    for i in range(10):  # 模拟多个任务
        future = executor.submit(foo, f"hello world! {i}")
        to_do.append(future)

    for future in as_completed(to_do):  # 并发执行
        print(future.result())