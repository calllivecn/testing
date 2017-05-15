#!/usr/bin/env python3
#coding=utf-8

import socket,ssl

s = socket.socket()
s = ssl.SSLSocket(sock=s,ssl_version=ssl.PROTOCOL_TLSv1_2)

s.connect(('',6789))

s.send('12345'.encode())

s.close()

