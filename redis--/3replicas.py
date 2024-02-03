#!/usr/bin/env python3
# coding=utf-8
# date 2024-02-03 18:29:03
# author calllivecn <c-all@qq.com>

"""
从无配置文件启动的3个节点中，动态的配置主从replication模式。
"""

import sys
import time

import redis

def configure_master_slave(master_host, master_port, slave_hosts, password: str = None):
    # 连接到主节点
    master = redis.Redis(host=master_host, port=master_port, password=password)

    # 获取主节点的信息
    master_info = master.info('replication')
    master_id = master_info['master_replid']

    # check master requirepass

    p = master.config_get("requirepass")

    masterauth = p.get("requirepass")

    # 配置从节点
    for slave_host, slave_port in slave_hosts:

        slave = redis.Redis(host=slave_host, port=slave_port)

        if masterauth is not None:
            print(f"master 有密码: {masterauth}")
            slave.config_set("masterauth", masterauth)

        slave.replicaof(master_host, master_port)

        # while (slave_info := slave.info('replication')["master_link_status"]) == "down":
        slave_info = slave.info('replication')
        while slave_info["master_link_status"] == "down":
            # print(f"wait ... master_link_status: {slave_info}")
            print(f"wait ... master_link_status ...")
            time.sleep(1)
            slave_info = slave.info('replication')


        if slave_info['master_replid'] == master_id:
            print(f"Slave at {slave_host}:{slave_port} configured successfully.")
        else:
            print(f"Failed to configure slave at {slave_host}:{slave_port}.")


if __name__ == "__main__":
    master_host = "10.1.3.1"
    master_port = 6379
    slave_hosts = [("10.1.3.1", 6380), ("10.1.3.1", 6381)]

    configure_master_slave(master_host, master_port, slave_hosts, password=sys.argv[1])

