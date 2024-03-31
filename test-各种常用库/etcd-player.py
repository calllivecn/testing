#!/usr/bin/env py3
#coding=utf-8
# date 2018-08-30 14:24:51
# author calllivecn <calllivecn@outlook.com>

import random

import etcd

#cli = etcd.Client(host='192.168.121.75',port=2379)
cli = etcd.Client(port=2379)

#result = cli.read('zx',recursive=True)
for i in range(100000):
    #suffix = random.randrange(1,999)
    result = cli.set(f"zx/{i}",i)
    print(result)

print("get -->", cli.get("zx-test").value)
