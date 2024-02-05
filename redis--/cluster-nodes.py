#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-05 17:26:06
# author calllivecn <calllive@outlook.com>

import sys
import time

import redis



r = redis.RedisCluster(host=sys.argv[1], port=sys.argv[2])

c = 0
while True:
    nodes_info = r.cluster_nodes()
    # info = r.info()
    # print(f"""keys: {info["keys"]}""")

    print(c, "="*20)
    for node, info in nodes_info.items():
        print(f"""{node}\tflags:{info["flags"]}\t{info["node_id"]}\t{info["master_id"]}""")

    c += 1
    time.sleep(1)

r.close()

