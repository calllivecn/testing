#!/usr/bin/env python3
# coding=utf-8
# date 2021-12-25 22:18:58
# author calllivecn <calllivecn@outlook.com>


"""
# 初始化握手包
msg.type = 0x01 # bytes(1)
msg.reserved = bytes(3)
msg.sender_index = bytes(4)
msg.ephemeral = bytes(32)
msg.timestmap = bytes(12)
msg.mac1 = bytes(16)
msg.mac2 = bytes(16)

# 响应握手包
msg.type = 0x02 # bytes(1)
msg.reserved = bytes(3)
msg.sender = bytes(4) # 目前使用 tcp 这个应该是可以不需要的。
msg.receiver = bytes(4)
msg.ephemeral = bytes(32)
msg.empty = bytes(32) # 全0
msg.mac1 = bytes(16)
msg.mac2 = bytes(16)

# 有时候可能 的 cookie 包
msg.type = 0x03 # bytes(1)
msg.reserved = bytes(3)
msg.receiver = bytes(4)
msg.nonce = bytes(24)
msg.cookie = bytes(16)


# 传输数据包
msg.type = 0x04 # bytes(1)
msg.reserved = bytes(3)
msg.receiver = bytes(4)
msg.counter = bytes(8)
msg.packet = AEAD (Authenticated encryption with associated data)


# 本地需要维护的结构
Peer : 4byte 索引。
S(priv), S(pub): 静态密钥对，
E(priv), E(pub): 临时的密钥对，
Q : 可选的预先共享私钥，
H : 一个hash结果值，
C : chaing key (相当于区块链)
T(send), T(recv): 发送和接收的对称密钥，
N(send), N(recv): 用于发送和接收的随机计数器(nonce)
"""


import struct



class ProtoFmt:

    def __init__(self):
        pass

    
    def handsshake(self):
        """
        初始化握手包
        """
        self.type = 0x01
        self.reserved = bytes(3)
        self.sender_index = bytes(4)
        self.ephemeral = bytes(32)
        self.timestmap = bytes(12)
        self.mac1 = bytes(16)
        self.mac2 = bytes(16)

    def parsepack(self):
        pass
