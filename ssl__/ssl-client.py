#!/usr/bin/env python3
#coding=utf-8

import socket,ssl

s = socket.socket()
s = ssl.SSLSocket(sock=s,ssl_version=ssl.PROTOCOL_TLSv1_2)

s.connect(('',6789))

print('recv --> testing TLS1_2')
s.send('testing TLSv1_2'.encode())
s.recv(1024)
s.close()

