#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-03 12:33:42
# author calllivecn <c-all@qq.com>


import os
import sys
import ssl
import time
import socket
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
from redis.backoff  import NoBackoff, ExponentialBackoff
from redis.cluster import ClusterNode



# 创建一个 Redis 集群节点列表, startup_nodes
nodes = [
    ClusterNode('172.20.1.1', 6379),
    ClusterNode('172.20.1.2', 6379),
    ClusterNode('172.20.1.3', 6379),
    ClusterNode('172.20.1.4', 6379),
    ClusterNode('172.20.1.5', 6379),
    ClusterNode('172.20.1.6', 6379),
]


# usercfg = redis.UsernamePasswordCredentialProvider("default", "linux")

def generate() -> Tuple[str, bytes]:
    n = random.randint(16, 128)
    return binascii.b2a_hex(ssl.RAND_bytes(6)).decode(), ssl.RAND_bytes(n)



def test_write(args):
    """
    在集群中master 节点 挂掉时，对应的slave自动顶上。
    这期间客户端会block住，直到超时后恢复。超时时间是参数socket_timeout
    """


    # socket.timeout  在 py3.8 是和 TimeoutError 是不同的 到py3.10 就是一样的了。py3.9 是不是一样不知道。
    retry = Retry(ExponentialBackoff(), 3) 
    # retry.update_supported_errors([exceptions.ResponseError, exceptions.ClusterError])

    # Redis Cluster client with retries
    r = RedisCluster(host=args.host, port=args.port, password=args.password,
                     retry=retry, cluster_error_retry_attempts=3,
                     socket_timeout=5,
                    #  protocol=3, # 使用 3, 在集群 reshard 时。 会报: ReseponseError。 
                     )

    t = time.time()
    count_err = 0
    speed_position = 0
    for i in range(args.write):

        key, value = generate()
        key = f"number-{i}"
        # r.set(key, value)
        if r.setex(key, 60, value):
            pass
        else:
            count_err += 1
        
        t2 = time.time()
        interval = t2 - t
        if interval > 1:
            interval_human = round(t2 - t, 3)
            speed = i - speed_position
            speed_position = i
            print(f"当前执行了: {i}/{args.write}, 速度：{speed}/s, 总共设置key失败次数: {count_err}, 耗时: {interval_human}/s")
            t = t2

    r.close()


def test_read(args):
    # retry = Retry(NoBackoff(), 3)
    retry = Retry(ExponentialBackoff(), 3)

    r = RedisCluster(host=args.host, port=args.port, password=args.password,
                    #  retry=retry,
                    #  cluster_error_retry_attempts=3,
                    #  socket_timeout=5,
                     )

    t = time.time()
    count_err = 0
    speed_position = 0
    for i in range(args.read):
        key=f"number-{i}"
        value = r.get(key)

        if value is None:
            count_err += 1

        t2 = time.time()
        interval = t2 - t
        if interval > 1:
            interval_human = round(t2 - t, 3)
            speed = i - speed_position
            speed_position = i
            print(f"当前执行了: {i}/{args.read}, 速度：{speed}/s, 总共获取key不存在次数: {count_err}, 耗时: {interval_human}/s")
            t = t2

    r.close()


def main():

    import argparse

    parse = argparse.ArgumentParser(
        usage="%(prog)s <--read|--write count>"
    )

    parse.add_argument("--password", action="store", help="集群的密码")
    parse.add_argument("--host", action="store", help="集群的地址: ip:port")
    parse.add_argument("--port", action="store", type=int, default=6379, help="集群的地址: ip:port")

    parse.add_argument("--read", action="store", type=int, help="读取多少key")
    parse.add_argument("--write", action="store", type=int, help="写入多少key")

    args = parse.parse_args()

    if args.read:
        test_read(args)

    elif args.write:
        test_write(args)
    else:
        print("需要参数")
        parse.print_help()



if __name__ == "__main__":
    main()

