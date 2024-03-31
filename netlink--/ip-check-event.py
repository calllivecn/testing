#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-24 04:08:49
# author calllivecn <calllivecn@outlook.com>

import os
import socket
import struct
import atexit
import pprint


# 定义一些常量 
# 参考文件：include/linux/netlink.h
# 参考文件：include/linux/rtnetlink.h
# man 7 rtnetlink

RTMGRP_LINK = 0x1 # 监听网络接口变化的组
RTMGRP_IPV4_IFADDR = 0x10
RTMGRP_IPV6_IFADDR = 0x100

# 定义一些常量
NLMSG_NOOP = 1 # netlink消息类型：空操作
NLMSG_ERROR = 2 # netlink消息类型：错误
RTM_NEWLINK = 16 # netlink消息类型：新建网络接口
RTM_DELLINK = 17 # netlink消息类型：删除网络接口
RTM_NEWADDR = 20 # netlink消息类型：接口添加ip地址
RTM_DELADDR = 21 # netlink消息类型：接口删除ip地址

IFLA_IFNAME = 3 # 接口属性类型：名称

IFA_F_TENTATIVE = 0x40 # 接口标志：tentative; tentative表示地址还在进行重复地址检测（DAD）



# # 解析netlink消息头部（长度为16字节），得到长度、类型、标志、序列号、进程ID等信息
msg_header = struct.Struct("=LHHLL")
fields = ("msg_len", "msg_type", "flags", "seq", "pid")

# 解析剩余数据中的前16个字节，得到协议族、设备类型、索引、标志、改变等信息
msg_header2 = struct.Struct("=BBHiII")
fields2 = ("family", "unknown", "if_type", "index", "flags", "change") 


# 解析后面的字段，
"""
struct rtattr {
    unsigned short rta_len;  /* Length of option */
    unsigned short rta_type; /* Type of option */
    /* Data follows */
};
"""

# attr_type
IFA_IFNAME = 8 #接口名称


IF_TYPE_ADDR_IPV4 = 128
IF_TYPE_ADDR_IPV6 = 192


# 创建netlink套接字并绑定本地地址
sockfd = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
# sockfd.bind((os.getpid(), RTMGRP_LINK | RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR))
sockfd.bind((0, RTMGRP_LINK | RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR))

atexit.register(sockfd.close)

while True:
    # 接收消息
    data = sockfd.recv(65535)
    content = dict(zip(fields ,msg_header.unpack(data[:16])))
    # content["data"] = data


    # 去掉netlink消息头部，得到剩余数据（长度为msg_len-16字节）
    content2 = dict(zip(fields2, msg_header2.unpack(data[16:32])))
    # print("="*40)

    content2.update(content)
    flags = content2["flags"]
    content2["flags"] = hex(flags)
    
    """
    # 检查消息类型并处理相应事件
    # if msg_type == 16: # RTM_NEWADDR

    ~~RTM_ADDADDR 目前 还有点问题，直接这样会 add 两次，头次会 tentative 地址冲突检测（DAD）~~
    
    这很可能是因为您添加的 IPv6 地址是双栈地址。双栈地址是同时支持 IPv4 和 IPv6 的地址。当您添加一个双栈地址时，会产生两个 msg_type == 20 and (if_type == 192, 128)的数据包。
    第一个数据包是添加 IPv4 地址的通知，第二个数据包是添加 IPv6 地址的通知。

    如果您想了解更多关于双栈地址的信息，您可以参考RFC 4213。
    """

    if content["msg_type"] == RTM_NEWADDR and content2["if_type"] == IF_TYPE_ADDR_IPV6:
        print("IPv6 address added")

    elif content["msg_type"] == RTM_NEWADDR and content2["if_type"] != IF_TYPE_ADDR_IPV6:
        print("IPv4 address added")

    elif content["msg_type"] == RTM_DELADDR:
        print("IP address removed")
    else:
        print(f"""{content["msg_type"]=}""")

    print("content", "="*40)
    # pprint.pprint(content2, sort_dicts=False)
    pprint.pprint(content2)

    # 这个实测不对。
    # state = 'up' if content["flags"] & 1 else 'down' 

    # 这个实测不对。
    tentative = 'tentative' if flags & IFA_F_TENTATIVE else 'no tentative' # 根据标志判断是否tentative

    print("tentative:", tentative)

    # 解析 netlink 消息属性。 后面的数据是 attr_type: 2B, attr_len: 2B, attr_value: payload
    print("解析 netlink 消息属性。")
    cur = 32
    while cur < content["msg_len"]:
        print("-"*20)
        attr_type, attr_len = struct.unpack("=HH", data[cur:cur+4])
        cur += 4
        attr_value = data[cur:cur+attr_len]
        print("attr_type:", attr_type)
        print("attr_len:", attr_len)
        print("attr_value:", attr_value)
        cur += attr_len
    
    print("="*40)


