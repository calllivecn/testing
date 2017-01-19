#!/usr/bin/env python3
#coding=utf-8


import socket,threading,sys
import multiprocessing as mp


count=int(sys.argv[1])


def connect(host,port,content):
	count=0
	for i in range(content):
		sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
		sock.connect((host,port))
		sock.send(str(content).encode())
		data = sock.recv(1024)
		#sock.shutdown(socket.SHUT_RDWR)
		sock.close()
		count+=1
	print('这一个进程一共连接{}次'.format(count),flush=True)

def th(count):
	for i in range(count):
		t1=threading.Thread(target=connect,args=('127.0.0.1',6789,100000))
		t1.start()

def multiprocessing(count):
	for i in range(count):
		multiprocess = mp.Process(target=connect,args=('127.0.0.1',6789,100000))
		multiprocess.start()
		#multiprocess.join()

try:
	for i in range(1,1+int(sys.argv[1])):
		multiprocessing(1)
	#multiprocessing(int(sys.argv[1]))
	
except KeyboardInterrupt:
	print("ctrl+C exit...")


