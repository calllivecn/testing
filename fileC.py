#!/usr/bin/env python3
#coding=utf-8

import sys,socket,os


file_size=os.stat(sys.argv[1]).st_size

print('开始发送文件：{}"\t"大小为：{}'.format(sys.argv[1],file_size))


FILE_INFO=sys.argv[1]+','+str(file_size)

print(FILE_INFO)

BUF=4096

ADDR=('0.0.0.0',6789)

C=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def send_file_info():
	try:
		number=C.sendto(FILE_INFO.encode('utf-8'),ADDR)
		if not number: return -1
		C.settimeout(15)
		data,address = C.recvfrom(BUF)
		data=data.decode('utf-8')
		if data !='OK!': 
			print('返回超时。')
		C.settimeout(None)
		
	except:
		print('有收发异常。')
		sys.exit(1)
		C.close()


C.sendto(FILE_INFO.encode('utf-8'),ADDR)

C.settimeout(15)

data,address = C.recvfrom(BUF)
data=data.decode('utf-8')

if data !='OK!': 
	print('返回超时。')

C.settimeout(None)

f_send=open(sys.argv[1],'rb')


while file_size > 0:
	if file_size > BUF:
		send_data=f_send.read(BUF)
		file_size=file_size-BUF
		C.sendto(send_data,ADDR)
	else:
		send_data=f_send.read(file_size)
		file_size=file_size-len(data)
		C.sendto(send_data,ADDR)

print('发送完成。')

C.close()


