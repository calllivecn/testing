#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-09 11:29:44
# author calllivecn <calllivecn@outlook.com>

import time

# main.py
from tasks import (
    add,
    sleep,
)

# 异步调用加法任务
result = add.delay(4, 4)

#print("use backend:", result.backend)

# 获取返回值
# while (ready := result.ready()) is False:
#     time.sleep(1)
#     print(f"waiting ...")

print(result.get())

result = sleep.delay(5)
print(result.id, result.get())

