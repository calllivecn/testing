#!/usr/bin/env python3
#coding=utf-8

import socket

if "__main__" == __name__:


    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.connect(('localhost',8008))
    sock.send(' 中文字显示 this is test send()'.encode('utf-8'))
    
    szBuf = sock.recv(1024)
    byt = 'recv:' + szBuf.decode('utf-8')
    print(byt)
    
    sock.close()
    print('end of the connecct')
