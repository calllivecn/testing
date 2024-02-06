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
from redis import (
    RedisCluster,
    exceptions,
)
from redis.retry import Retry
from redis.backoff  import ExponentialBackoff
from redis.cluster import ClusterNode



# 创建一个 Redis 集群节点列表, startup_nodes
nodes = [
    ClusterNode('172.20.1.2', 6379),
    ClusterNode('172.20.1.3', 6379),
    ClusterNode('172.20.1.4', 6379),
    #ClusterNode('172.20.1.5', 6379),
    #ClusterNode('172.20.1.6', 6379),
    #ClusterNode('172.20.1.7', 6379),
]


# usercfg = redis.UsernamePasswordCredentialProvider("default", "linux")

def generate() -> Tuple[str, bytes]:
    n = random.randint(16, 128)
    return binascii.b2a_hex(ssl.RAND_bytes(6)).decode(), ssl.RAND_bytes(n)

key_prefix="test-"


def test_write(count=10000):

    for i in range(count):

        if i % 1000 == 0:
            print(f"当前执行了: {i}/{count}")

        key, value = generate()
        #r.set(key_prefix + key, value)
        r.setex(key_prefix + key, 120, value)
        #try:
        #    r.setex(key_prefix + key, 60, value)
        #except exceptions.ConnectionError:
        #    print("发生切换？")


def test_read():

    for i in range(1000000):
        key=f"number-{i}"
        print(f"{key=} value={r.get(key)}")
        #r.get(key)

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

    #nodes = [ClusterNode(args.host, args.port)]
    # redis_conn = RedisCluster(host=args.host, port=args.port, password=args.password)
    # nodes = redis_conn.get_nodes()
    # redis_conn.close()

    global r
    # 这样 在集群中有节点故障时（不分master, replication), 都会卡住。(startup_nodes的原因？)
    #r = RedisCluster(startup_nodes=nodes, password=args.password, protocol=3, socket_timeout=5)

    # ~~直接使用host 配置，让它自己连接其他节点。这样是会影响的。需要先连接一个节点,拿到所有节点的地址。在重新初始化一个startup_nodes=~~
    # ~~现在看  好像和server 端的 io-threads 有关？？？？~~

    # r = RedisCluster(host=args.host, port=args.port, password=args.password, protocol=3)


    retry = Retry(ExponentialBackoff(), 3)
    r = RedisCluster(host=args.host, port=args.port, password=args.password, retry=retry, protocol=3)

    atexit.register(r.close)

    if args.read:
        test_read()

    elif args.write:
        test_write(args.write)
    else:
        print("需要参数")
        parse.print_help()



if __name__ == "__main__":
    main()

