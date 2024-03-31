#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-24 14:40:53
# author calllivecn <calllivecn@outlook.com>

import etcd

conn = etcd.Client("192.168.224.172", port=2379)

#subtree = conn.read("/test/", recursive=True, sorted=True)
subtree = conn.read("/jenkinsjob", recursive=True)

for k in subtree.children:
    if not k.dir:
        print(k.key, k.value)


