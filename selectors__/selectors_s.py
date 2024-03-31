#!/usr/bin/env python3
#coding=utf-8
# date 2017-11-04 09:37:33
# author calllivecn <calllivecn@outlook.com>


from socket import socket,SOL_SOCKET,SO_REUSEPORT

listen=('0.0.0.0',6789)
listen=('192.168.10.2',6789)

s = socket()
s.setsockopt(SOL_SOCKET,SO_REUSEPORT,1)
s.bind(listen)
s.listen(128)
try:
    sock , addr = s.accept()
    print(addr)
    while True:
        c=0
        data=b''
        while c < 4096:
            data+=sock.recv(4096)
            c+=len(data)
            if c == 0:
                exit(0)
        #print('接收数:',4096)
        c=0
        while c < 4096:
            c+=sock.send(data)
except KeyboardInterrupt:
    exit(0)
finally:
    sock.close()
    s.close()
