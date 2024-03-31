#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-09 11:29:22
# author calllivecn <calllivecn@outlook.com>

import time

# tasks.py
from celery import Celery



# 创建一个Celery实例
#app = Celery('tasks', broker='amqp://guest@localhost//', backend='db+sqlite:///results.sqlite')

app = Celery('tasks', broker='redis://localhost:6379', backend='redis://localhost')

app.conf.broker_connection_retry_on_startup=True

# 定义一个加法任务
@app.task
def add(x, y):
    return x + y


@app.task
def sleep(t):
    time.sleep(t)
    print("这里能输出吗？")
    return t
