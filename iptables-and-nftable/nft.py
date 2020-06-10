#!/usr/bin/env python3
# coding=utf-8
# date 2020-06-10 14:47:07
# author calllivecn <c-all@qq.com>

import json
import ipaddress
from pprint import pprint

from nftables import Nftables


class NftableError(Exception):
    pass

def nft(cmd):

    nft = Nftables()
    
    nft.set_json_output(1)
    
    rc, output, err = nft.cmd(cmd)

    if rc != 0:
        raise NftableError(f"执行错误: {err}")

    return output


#summary = json.loads(output)

#pprint(summary)

def check(rule):

    nft = Nftables()
    nft.set_json_output(1)
    rc, rules, err = nft.cmd(f"list table ip easywg")
    if rc != 0:
        raise NftableError(f"执行错误: {err}")

    pprint(json.loads(rules))


def add_forwarding(ifname, network):

    try:
        net = ipaddress.ip_network(network)
    except ValueError:
        raise NftableError(f"网络地址不正确：{network}")

    for ip46 in ("ip", "ip6"):
    
        output = nft(f"add table {ip46} easywg")
        
        output = nft(f"add chain {ip46} easywg postrouting {{ type nat hook postrouting priority 10; policy accept; }}")
        
        if ip46 == "ip" and net.version == 4:
            output = nft(f"add rule {ip46} easywg postrouting oif {ifname} {ip46} saddr {network} counter masquerade")
        elif ip46 == "ip6" and net.version == 6:
            output = nft(f"add rule {ip46} easywg postrouting oif {ifname} {ip46} saddr {network} counter masquerade")


check("ip")
#add_forwarding("enp2s0", "10.1.1.0/24")

