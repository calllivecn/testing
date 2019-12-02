#!/usr/bin/env py3
#coding=utf-8
# date 2018-09-09 14:43:22
# author calllivecn <c-all@qq.com>

import logging

from threading import Thread
from pprint import pprint

import bluetooth as bh

def server_socket(sock, info):
    recv_data = sock.recv(2014).decode()
    print(f"[{recv_data}] --> {info}")
    sock.send("我收到了你的消息".encode())
    sock.close()



bh_socket= bh.BluetoothSocket(bh.RFCOMM)
bh_socket.bind(("",1))
bh_socket.listen(1)

while True:
    b_sock, info = bh_socket.accept()
    print(str(info[0]) + " -- Connected!")

    t = Thread(target=server_socket,args=(b_sock, info[0]),daemon=True)
    t.start()

"""
# 扫描蓝牙
devices = bh.discover_devices(lookup_names=True)

i=1
for addr , name in devices:
    print("编号:", i, "蓝牙地址:", addr, "蓝牙名称:", name)
    i += 1

    #srvs = bh.find_service(address=addr)

    #for svc in srvs:
    #    print("前缀--->")
    #    pprint(svc)
"""
