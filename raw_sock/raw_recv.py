#!/usr/bin/env python3
#coding=utf-8


import socket
import sys

s = socket.socket(socket.AF_INET,socket.SOCK_RAW,98)

data, address = s.recvfrom(1024)

print('recv data:', data)
print('data length:', len(data))
print('IP :', address)


