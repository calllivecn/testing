#!/usr/bin/env python3 
#coding=utf-8

import socket,time,sys

ADDR = ('127.0.0.1',6789)

N=int(sys.argv[1])

ADDR_flag=True

for i in range(N):
	s = socket.socket()
	s.connect(ADDR)
	'''
	local_ADDR = s.getsockname()
	ADDR_flag=False
	else:
		s.bind(local_ADDR)
		s.connect(ADDR)
	'''	
	s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
	s.send(str(i).encode())
	data = s.recv(1024)
	if not data:
		s.close()
		break
	print(data)
	s.close()



