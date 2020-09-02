#!/usr/bin/env python3

import socket,sys

print(type(sys.argv),sys.argv)


s=socket.socket(socket.AF_INET,socket.SOCK_RAW,98)

try:
    data=sys.argv[2]
except IndexError:
    data='hello world!'

try:
    ip=sys.argv[1]
except IndexError:
    ip='127.0.0.1'

print('\ndata: ', data, 'ip :', ip)
s.sendto(data.encode(),(ip,0))

