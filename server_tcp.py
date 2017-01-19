#!/usr/bin/env python3 
#coding=utf-8

from multiprocessing.reduction import send_handle,recv_handle
from multiprocessing import Process,Pipe

import socket



def worker(in_pipe,out_pipe):
	try:
		out_pipe.close()
		while True:
			fd = recv_handle(in_pipe)
			print('接收到文件描述符 : ',fd)
			s = socket.socket(socket.AF_INET,socket.SOCK_STREAM,fileno=fd)
			s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
			while True:
				msg = s.recv(1024)
				if not msg:
					break
				print('worker 接收到数据{}'.format(msg))
				s.send(msg)
		
			#s.shutdown(socket.SHUT_RDWR)
			s.close()
	except KeyboardInterrupt:
		return 0
	finally:
		s.close()

def server(address,in_pipe,out_pipe,worker_pid):
	try:
		in_pipe.close()
		s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
		s.bind(address)
		s.listen(5)
		while True:
			client , addr = s.accept()
			print('server 收到连接{}'.format(addr))
			send_handle(out_pipe,client.fileno(),worker_pid)
			#client.shutdown(socket.SHUT_RDWR)
			client.close()
	except KeyboardInterrupt:
		return 0
	finally:
		s.close()


if __name__ == '__main__':
	c1,c2 = Pipe()
	worker_p = Process(target=worker,args=(c1,c2))
	worker_p.start()
	server_p = Process(target=server,args=(('',6789),c1,c2,worker_p.pid))
	server_p.start()
	c1.close()
	c2.close()

	


