#!/usr/bin/env python3
# coding=utf-8

import socket
import time
import sys

buf = 1024

IP_address = ''

PORT = 6789

try:
    exec(open(sys.argv[0]+'.cfg').read())
except Exception:
    print('读取配置文件异常')

BIND = (IP_address, PORT)

try:
    udp_S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_S.bind(BIND)
except Exception:
    print('有初始化异常')
    raise
else:
    print('SOCKET 初始化成功。')

try:
    while 1:
        data, address = udp_S.recvfrom(buf)
        data = 'recvfrom :'+data.decode('utf-8')
        if data == 'recvfrom :quit':
            break
        print(time.ctime(), 'address: ', address, data)
        udp_S.sendto(b'OK!', address)
except Exception as e:
    print('E : ', e)
    print('有收发异常。')

finally:
    udp_S.close()
