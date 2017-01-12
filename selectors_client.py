#!/usr/bin/env python3
#coding=utf-8


import socket,threading,sys

count=int(sys.argv[1])


def connect(host,port,content):
	sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
	sock.connect((host,port))
	sock.send(str(content).encode())
	data = sock.recv(1024)
	print(data.decode(),flush=True)
	sock.close()


def th(count):
	t1=threading.Thread(target=connect,args=('127.0.0.1',6789,count))
	t1.start()


try:
	for i in range(int(sys.argv[1])):
		th(i)
except KeyboardInterrupt:
	print("ctrl+C exit...")


