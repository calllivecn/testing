#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-09 11:29:44
# author calllivecn <c-all@qq.com>

# main.py
from tasks import add

# 异步调用加法任务
result = add.delay(4, 4)

# 获取返回值
print(result.get())

