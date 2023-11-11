#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-27 15:16:56
# author calllivecn <c-all@qq.com>

import time

import etcd3

# 配置 etcd 服务器地址
client = etcd3.client(
    host="10.1.2.1",
    # 设置超时时间
    timeout=5.0,
)

# 使用客户端
start = time.time()
for i in range(10000):

    client.put(f"key{i}", "value{i}")

client.close()

end = time.time()

print(f"耗时：{round(end - start, 2)}")

