#/usr/bin/env python3
#coding=utf-8

import sys,socket,threading

listen_addr = ('0.0.0.0',6789)

A_list=[]

A_list_lock = threading.Lock()

def server(S,ADDR):
		data = S.recv(1024)
		if data.decode('utf-8') == 'password':
				S.send('OK! 157'.encode('utf-8'))
		else:
				S.close()
				return -1

		data = S.recv(1024)
		if data.decode('utf-8') == 'client-A':
				global A_list
				if A_list_lock.acquire():
						A_list.append(ADDR)
						A_list_lock.release()


		if data.decode('utf-8') == 'client-B':
				S.send(str(len(A_list)).encode('utf-8'))
				
				for v1,v2 in A_list:
						v=v1+','str(v2).encode('utf-8')
						S.send(v)
				

		S.close()						

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

#s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

s.bind(listen_addr)

print('bind :',listen_addr)

s.listen(5)

print('正在监听。。。')

while True:
		s2,address=s.accept()
		print('addrees : {}\tClient-A number : {}'.format(address,len(A_list)))
		t = threading.Thread(target=server,args=(s2,address))
		t.start()


#s2.clos()
s.close()

print('server exit.')
