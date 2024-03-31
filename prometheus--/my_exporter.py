#!/usr/bin/env python3
# coding=utf-8
# date 2023-12-26 11:54:18
# author calllivecn <calllivecn@outlook.com>


import time
import random

from prometheus_client import (
    start_http_server,
    Gauge,
)


# 定义数据类型，metric, descrbie(描述), 标签
node_cpu_temp = Gauge('node_cpu_temp', "自定义查询cpu温度", ["instance"])

def get():
    start_http_server(8000)

    while True:
        itemkey = "instance"
        value = random.randint(-20, 120)

        node_cpu_temp.labels("temp").set(value)
        node_cpu_temp.labels("intance").set(value)

        time.sleep(5)



if __name__ == "__main__":
    get()

