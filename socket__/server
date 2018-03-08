#!/usr/bin/env python3
#coding=utf-8

#this is the server
import socket

if "__main__" == __name__:
    try:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        print("create socket suc!")
        
        sock.bind(('localhost',8008))
        print('bind socket suc!')
 
        sock.listen(5)
        print('listen socket suc!')      
        
    except:
        print("init socket err!")

        
    while True:
        print('listren for client...')
        conn,addr = sock.accept()
        print('get client')
        print(addr)
        
        conn.settimeout(5)
        szBuf = conn.recv(1024)
        byt = 'recv:' + szBuf.decode('utf-8')
        print(byt)
        
        if '0' == szBuf:
            conn.send('exit'.encode('utf-8'))
        else:
            conn.send('welcome client!'.encode('utf-8'))
        
        conn.close()
        print('end of the service')
