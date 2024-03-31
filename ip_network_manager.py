#!/usr/bin/env python3
# coding=utf-8
# date 2020-07-01 20:37:08
# author calllivecn <calllivecn@outlook.com>


import ipaddress


ten24 = ipaddress.IPv4Network("10.1.1.0/24")

net_addr = ipaddress.IPv4Network(int(ten24.network_address) + (1<<(32 - ten24.prefixlen)))


new_network = ipaddress.IPv4Network(net_addr.exploded.split("/")[0] + "/24")

print(new_network)
