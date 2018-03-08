#!/usr/bin/env python3
#coding=utf-8


import socket,fcntl,struct

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

ip = fcntl.ioctl(sock.fileno(),0x8915,struct.pack('64s',b'eth0'))

print(ip)

ip = socket.inet_ntoa(ip[20:24])

print(ip)


if_list = fcntl.ioctl(sock.fileno(),0x8912,struct.pack('i64s',0,b''))

print(struct.unpack('i',if_list[0:4]))
