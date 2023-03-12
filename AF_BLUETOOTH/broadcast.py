#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-12 21:17:12
# author calllivecn <c-all@qq.com>

import socket

"""
#import pydbus

# get the bluetooth adapter address
bus = pydbus.SystemBus()
adapter = bus.get('org.bluez', '/org/bluez/hci0')
adapter_addr = adapter.Address
"""

# create a bluetooth socket
#broadcast_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_DGRAM, socket.BTPROTO_RFCOMM)
broadcast_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_DGRAM, socket.BTPROTO_L2CAP)

# set the socket option to allow broadcast
broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# send a broadcast packet
dest_addr = "FF:FF:FF:FF:FF:FF" # the broadcast address
dest_port = 0x1001 # the destination port(术语:PSM)有两个范围：(保留/已知端口): 1~4095,(动态分配)： 4097-32765
data = "Hello, world!" # the data to send
broadcast_sock.sendto(data.encode(), (socket.BDADDR_LOCAL, dest_port))
print("Sent broadcast packet to", dest_addr)

# close the socket
broadcast_sock.close()

