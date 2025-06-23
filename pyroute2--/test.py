#!/usr/bin/env python3
# coding=utf-8
# date 2020-05-26 09:42:40
# author calllivecn <calllivecn@outlook.com>

import sys
import socket
from pprint import pprint

import pyroute2


def main():
    ifname = sys.argv[1]
    with pyroute2.IPRoute() as ipr:

        # 这样返回的是空: [],  如果要拿到ipv6 需要先拿到index ？
        
        iface_info: list = ipr.get_addr(label=ifname)
        pprint(f"debug: {iface_info=}")

        #index = iface_info[0].get_attr("IFA_LABEL")
        index = iface_info[0]["index"]
        print(f"{index=}")
        
        # 这很奇怪，使用label=iface_name 的方式拿不到ipv6...
        ipv6_info = ipr.get_addr(index=index, family=socket.AF_INET6)
        print("debug ipov6:")
        pprint(ipv6_info)



if __name__ == "__main__":
    main()
