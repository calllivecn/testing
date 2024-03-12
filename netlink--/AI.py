
import os
import enum
import socket
import struct

# 定义Netlink消息头部结构体
class nlmsghdr(struct.Struct):
    def __init__(self):
        self.format = 'IHHI'
        self.length = struct.calcsize(self.format)

    def pack(self, nlmsg_len, nlmsg_type, nlmsg_flags, nlmsg_seq):
        return struct.pack(self.format, nlmsg_len, nlmsg_type, nlmsg_flags, nlmsg_seq)

    def unpack(self, data):
        return struct.unpack(self.format, data)

# 定义Netlink消息类型结构体
class ifaddrmsg(struct.Struct):
    def __init__(self):
        self.format = 'BBHIII'
        self.length = struct.calcsize(self.format)

    def pack(self, ifa_family, ifa_prefixlen, ifa_flags, ifa_scope, ifa_index):
        return struct.pack(self.format, ifa_family, ifa_prefixlen, ifa_flags, ifa_scope, ifa_index, 0)

    def unpack(self, data):
        return struct.unpack(self.format, data)

# 定义Netlink消息属性结构体
class rtattr(struct.Struct):
    def __init__(self):
        self.format = 'HH'
        self.length = struct.calcsize(self.format)

    def pack(self, rta_type, rta_len):
        return struct.pack(self.format, rta_type, rta_len)

    def unpack(self, data):
        return struct.unpack(self.format, data)

# 定义Netlink消息属性类型
class ifa(enum.Enum):
    IFA_UNSPEC = 0
    IFA_ADDRESS = 1
    IFA_LOCAL = 2
    IFA_LABEL = 3
    IFA_BROADCAST = 4
    IFA_ANYCAST = 5
    IFA_CACHEINFO = 6
    IFA_MULTICAST = 7
    IFA_FLAGS = 8
    IFA_RT_PRIORITY = 9
    IFA_TARGET_NETNSID = 10
    IFA_EXT_MASK = 11

# 定义Netlink消息类型
class nlmsg(enum.Enum):
    NLMSG_NOOP = 1
    NLMSG_ERROR = 2
    NLMSG_DONE = 3
    NLMSG_OVERRUN = 4
    NLMSG_MIN_TYPE = 0x10
    NLMSG_MAX_TYPE = 0x2f
    NLMSG_NEWADDR = 20
    NLMSG_DELADDR = 21
    NLMSG_GETADDR = 22
    NLMSG_NEWLINK = 16
    NLMSG_DELLINK = 17
    NLMSG_GETLINK = 18

# 定义Netlink消息标志
class nlm(enum.Enum):
    NLM_F_REQUEST = 1
    NLM_F_MULTI = 2
    NLM_F_ACK = 4
    NLM_F_ECHO = 8
    NLM_F_DUMP_INTR = 16
    NLM_F_DUMP_FILTERED = 32
    NLM_F_ROOT = 0x100
    NLM_F_MATCH = 0x200
    NLM_F_ATOMIC = 0x400
    NLM_F_DUMP = (NLM_F_ROOT | NLM_F_MATCH)

# 定义Netlink消息组
class rtgen(enum.Enum):
    RTMGRP_LINK = 1
    RTMGRP_NOTIFY = 2
    RTMGRP_NEIGH = 4
    RTMGRP_TC = 8
    RTMGRP_IPV4_IFADDR = 0x10
    RTMGRP_IPV4_MROUTE = 0x20
    RTMGRP_IPV4_ROUTE = 0x40
    RTMGRP_IPV6_IFADDR = 0x100
    RTMGRP_IPV6_MROUTE = 0x200
    RTMGRP_IPV6_ROUTE = 0x400
    RTMGRP_DECnet_IFADDR = 0x1000
    RTMGRP_DECnet_ROUTE = 0x4000
    RTMGRP_IPV6_PREFIX = 0x20000

# 定义Netlink socket
class NetlinkSocket:
    def __init__(self, groups):
        self.sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
        self.sock.bind((os.getpid(), groups))

    def send(self, data):
        self.sock.send(data)

    def recv(self, bufsize):
        return self.sock.recv(bufsize)

    def close(self):
        self.sock.close()

# 监听指定网络接口的IP地址变化
def listen_ipaddr_change(ifname):
    # 创建Netlink socket
    sock = NetlinkSocket(rt