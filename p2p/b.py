#!/usr/bin/env python3
#coding=utf-8

import socket,time

buf=1024

SERVER=('120.24.243.133',6789)

test_addr = ('127.0.0.1',6789)

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

c = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

c.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

s.connect(test_addr)

s.send('client-B'.encode('utf-8'))
print('send client-B...')
a_addr = s.recv(buf).decode('utf-8')

a_addr = a_addr.split(',')
a_ip = a_addr[0]
a_port = int(a_addr[1])
a_addr = (a_ip,a_port)

s_addr = s.getsockname()

c.bind(s_addr)

print('bind s_addr...')
while 1:
		try:
				print('connect...')
				c.connect(a_addr)
				break
		except:
				print('connect A.')	
				time.sleep(1)

while 1:
		data=str(input('>> '))
		
		c.send(data.encode('utf-8'))
		if data == 'quit':
				break


c.close()
s.close()






