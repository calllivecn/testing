#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-03 12:33:42
# author calllivecn <c-all@qq.com>


import os
import sys
import ssl
import atexit
import random
import binascii

from typing import (
    Tuple,
)

import redis
from redis import RedisCluster
from redis.cluster import ClusterNode



# 创建一个 Redis 集群节点列表, startup_nodes
nodes = [
    ClusterNode('172.22.1.2', 6379),
    ClusterNode('172.22.1.3', 6379),
    ClusterNode('172.22.1.4', 6379),
]


# usercfg = redis.UsernamePasswordCredentialProvider("default", "linux")

# 创建一个 Redis 集群连接池
# r = redis.RedisCluster(startup_nodes=nodes, password="linux")


def generate() -> Tuple[str, bytes]:
    n = random.randint(16, 128)
    return binascii.b2a_hex(ssl.RAND_bytes(6)).decode(), ssl.RAND_bytes(n)

key_prefix="test-"


def test_write(count=10000):

    for i in range(count):

        if i % 1000 == 0:
            print(f"当前执行了: {i}/{count}")

        key, value = generate()
        r.set(key_prefix + key, value)


def test_read():
    cursor = 0

    while True:
        nodes, list_response = r.scan(cursor, match=key_prefix + "*", count=1000, target_nodes=RedisCluster.REPLICAS)
        respnose_len = len(list_response)

        if respnose_len == 0:
            print("扫描完成...")
            break

        cursor += respnose_len

        print(f"当前已经扫描的key数量：{cursor}")

        for key in list_response:
            # print(f"{key=} value={r.get(key)}")
            r.get(key)

global r


def main():

    import argparse

    parse = argparse.ArgumentParser(
        usage="%(prog)s <--read|--write count>"
    )

    parse.add_argument("--password", action="store", help="集群的密码")
    parse.add_argument("--host", action="store", help="集群的地址: ip:port")
    parse.add_argument("--port", action="store", type=int, default=6379, help="集群的地址: ip:port")

    parse.add_argument("--read", action="store_true", help="读取所有key")
    parse.add_argument("--write", action="store", type=int, help="读取所有key")

    args = parse.parse_args()

    nodes = [ClusterNode(args.host, args.port)]

    global r
    # 这样 在集群中有节点故障时（不分master, replication), 都会卡住。
    redis_con = RedisCluster(startup_nodes=nodes, password=args.password, read_from_replicas=True)

    r = redis_con

    atexit.register(redis_con.close)

    if args.read:
        test_read()

    elif args.write:
        test_write(args.write)
    else:
        print("需要参数")
        parse.print_help()



if __name__ == "__main__":
    main()

