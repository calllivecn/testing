#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-09 11:29:22
# author calllivecn <c-all@qq.com>

# tasks.py
from celery import Celery

# 创建一个Celery实例
app = Celery('tasks', broker='amqp://guest@localhost//', backend='db+sqlite:///results.sqlite')

# 定义一个加法任务
@app.task
def add(x, y):
    return x + y

