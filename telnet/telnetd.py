#!/usr/bin/python3
#coding=utf-8

import subprocess,socket,time,threading

def order(sock):
	
	while 1:

		cmd=sock.recv(4096).decode('utf-8')
		if cmd=='exit' or cmd=='quit': break
		rev,out=subprocess.getstatusoutput(cmd)
		sock.send(out.encode('utf-8'))
	sock.close()

server=socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
server.bind(('127.0.0.1',6789))

server.listen(5)
try:
	while 1:
		sock,address=server.accept()
		th=threading.Thread(target=order,args=(sock,))
		th.start()

except KeyboardInterrupt:
	print('exit ok')
	exit(0)
