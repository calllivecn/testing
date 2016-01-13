#!/usr/bin/python3
#coding=utf-8

PS1='CMD$ '


import socket

client=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)

client.connect(('127.0.0.1',6789))

while 1:
	cmd=str(input(PS1))
	client.send(cmd.encode('utf-8'))
	if cmd == 'exit' or cmd == 'quit': 
		client.send(cmd.encode('utf-8'))
		break
	data=client.recv(4096)
	print(data.decode('utf-8'))

client.close()
