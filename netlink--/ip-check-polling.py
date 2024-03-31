#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-24 03:38:21
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import socket
import struct
import time
import fcntl

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])

def main(ifname):
    last_ip = None
    while True:
        ip = get_ip_address(ifname)
        if ip != last_ip:
            print('IP address changed to', ip)
            last_ip = ip
        time.sleep(1)

if __name__ == '__main__':

    try:
        ifname = sys.argv[1]
    except IndexError:
        print("需要指定接口名")
        sys.exit(1)

    if not os.path.exists(f"/sys/class/net/{ifname}"):
        print(f"{ifname}: 接口名不存在。。。")
        sys.exit(1)

    main(ifname)
