#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-05 17:26:06
# author calllivecn <calllive@outlook.com>

import sys
import time

import pprint

import redis


# 从集群模式中，拿到指定主节点的从节点。
def master_get_slave(nodes_info:dict):
    nodes_info

r = redis.RedisCluster(host=sys.argv[1], port=sys.argv[2], socket_timeout=5)

c = 0
try:
    while True:
        nodes_info = r.cluster_nodes()
        # clusterinfo = r.info()
        # print(f"""keys: {info["keys"]}""")

        # pprint.pprint(nodes_info)

        print(c, "="*20)

        masters = {}
        slaves_not_master = []
        for node, info in nodes_info.items():

            # 说明是master 节点
            if "master" in info["flags"]:
                masters[info["node_id"]] = {
                    "ip": node,
                    "flags": info["flags"],
                    "slots": info["slots"],
                    "slaves": [],
                }


        for node, info in nodes_info.items():
            # 说明是slave 节点
            if "slave" in info["flags"]:
                # 这个slave 有 master 节点
                if info["master_id"] != "-":

                    
                    m = masters.get(info["master_id"])  
                    if m is None:

                        slaves_not_master.append({
                            "node_id": info["node_id"],
                            "ip": node,
                            "flags": info["flags"],
                        })
                    
                    else:
                        m["slaves"].append({
                            "node_id": info["node_id"],
                            "ip": node,
                            "flags": info["flags"],
                        })

            # print(f"""{node} {info["node_id"]:<40} {info["master_id"]:<40} flags:{info["flags"]}\tslots:{info["slots"]}""")

        for master, info in masters.items():
            # print("+"*20)
            ip = info["ip"]
            flags = info["flags"]
            slots = info["slots"]
            slaves = info["slaves"]
            print(f"""M: {ip=} node_id:{master}\n\t{flags=}\n\t{slots=}""")
            
            for info in slaves:
                print("\tS:")
                node_id = info["node_id"]
                ip = info["ip"]
                flags = info["flags"]

                print(f"""\t{ip=} {node_id=} {flags=}""")
        

        for slave_not_master in slaves_not_master:
            print("没有主节点的从节点：")
            node_id = info["node_id"]
            ip = info["ip"]
            flags = info["flags"]

            print(f"""\t{ip=} {node_id=} {flags=}""")
    
        c += 1
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    r.close()

