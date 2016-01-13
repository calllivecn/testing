#!/usr/bin/env python3
#coding=utf-8
import socket,subprocess,time,threading

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
c = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
c.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

SERVER=('120.24.243.133',6789)

def connect_server(addr):
	#	s.settimeout(15)
		s.connect(addr)
		
		s.send('password'.encode('utf-8'))
		
		

def live(s):
		while True:
				s.send('live'.encode('utf-8'))
				time.sleep(1)
		
		
test_addr=('127.0.0.1',6789)

s.connect(test_addr)

#s.connect(SERVER)
		
s.send('client-A'.encode('utf-8'))
print('send client-A...')
b_addr = s.recv(1024).decode('utf-8')

b_addr = b_addr.split(',')

b_ip=b_addr[0]

b_port = int(b_addr[1])

b_addr = (b_ip,b_port)

		
#thread = threading.Thread(target=live,args=(s,),daemon=True)

#thread.start()

sockname = s.getsockname()

c.bind(sockname)
print( 'bind sockname...')
try:
		c.connect(b_addr)

except :
		print('connect B.')


c.listen(5)

s2,address = c.accept()
		
print('client :',address)

while True:		
		data = s2.recv(1024)
		data=data.decode('utf-8')
		print('RECV : ',data)
		if data == 'quit':
				break
c.close()
s2.close()
s.close()
		

#cmd = subprocess.getstatusoutput


#back,l = cmd()
