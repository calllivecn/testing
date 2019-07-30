#!/usr/bin/env python3
#coding=utf-8


import socket,threading,sys
import multiprocessing as mp

count=int(sys.argv[1])


def connect(host,port,content):
    count=0
    for i in range(content):
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,True)
        sock.connect((host,port))
        #sock.send(str(content).encode())
        sock.send(bytes(2048))
        data = sock.recv(4096)
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

from socket import socket,AF_INET,SOCK_STREAM,SO_REUSEPORT,SOL_SOCKET
def speed():
    size=4096
    block=bytes(size)
    raddr = ('127.0.0.1',6789)
    raddr = ('192.168.10.2',6789)
    raddr = ('192.168.10.1',6789)
    try:
        s = socket()
        #s.setsockopt(SOL_SOCKET,SO_REUSEPORT,1)
        s.connect(raddr)
        for i in range(int(sys.argv[1])):
            c=0
            while c < size:
                c+=s.send(block)
            c=0
            while c < size:
                c+=len(s.recv(size))
    finally:
        s.close()

