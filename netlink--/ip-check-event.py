#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-24 04:08:49
# author calllivecn <c-all@qq.com>

import os
import socket
import struct
import atexit
import pprint


# 定义一些常量 
# 参考文件：include/linux/netlink.h
# 参考文件：include/linux/rtnetlink.h
# man 7 rtnetlink

RTMGRP_LINK = 1 # 监听网络接口变化的组
RTMGRP_IPV4_IFADDR = 0x10
RTMGRP_IPV6_IFADDR = 0x100

# 定义一些常量
NLMSG_NOOP = 1 # netlink消息类型：空操作
NLMSG_ERROR = 2 # netlink消息类型：错误
RTM_NEWLINK = 16 # netlink消息类型：新建网络接口
RTM_DELLINK = 17 # netlink消息类型：删除网络接口
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


# 创建netlink套接字并绑定本地地址
sockfd = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
# sockfd.bind((os.getpid(), RTMGRP_LINK | RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR))
sockfd.bind((0, RTMGRP_LINK | RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR))

atexit.register(sockfd.close)

while True:
    # 接收消息
    data = sockfd.recv(65535)
    content = dict(zip(fields ,msg_header.unpack(data[:16])))
    content["data"] = data

    print("="*40)
    pprint.pprint(content, sort_dicts=False)
    
    # 检查消息类型并处理相应事件
    # if msg_type == 16: # RTM_NEWADDR
    if content["msg_type"] == 20: # RTM_ADDADDR 目前 还有点问题，直接这样会 add 两次，头次会 tentative 地址冲突检测（DAD）
        print("IP address added")
    elif content["msg_type"] == 21: # RTM_DELADDR
        print("IP address removed")
    else:
        print(f"""msg_type {content["msg_type"]}""")
    

    # 去掉netlink消息头部，得到剩余数据（长度为msg_len-16字节）
    content2 = dict(zip(fields2, msg_header2.unpack(data[16:32])))
    # print("="*40)

    pprint.pprint(content2, sort_dicts=False)

    # 这个实测不对。
    state = 'up' if content["flags"] & 1 else 'down' 

    # 这个实测不对。
    tentative = 'tentative' if content2["flags"] & IFA_F_TENTATIVE else 'no tentative' # 根据标志判断是否tentative

    print("if_index:", content2["index"], "state:", state, "tentative:", tentative)



