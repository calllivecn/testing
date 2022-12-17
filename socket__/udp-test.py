#!/usr/bin/env python3
# coding=utf-8

import socket
import time
import sys

buf = 1024

IP_address = ''

PORT = 6789

def server():

    try:
        exec(open(sys.argv[0]+'.cfg').read())
    except Exception:
        print('读取配置文件异常')

    BIND = (IP_address, PORT)

    try:
        udp_S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_S.bind(BIND)
    except Exception:
        print('有初始化异常')
        raise
    else:
        print('SOCKET 初始化成功。')

    try:
        while True:
            data, address = udp_S.recvfrom(buf)
            data = 'recvfrom :'+data.decode('utf-8')
            if data == 'recvfrom :quit':
                break
            print(time.ctime(), 'address: ', address, data)
            udp_S.sendto(b'OK!', address)
    except Exception as e:
        print('E : ', e)
        print('有收发异常。')

    finally:
        udp_S.close()

def client():

    addr = sys.argv[1]
    port = sys.argv[2]
    
    try:

        udp_C = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print('有初始化异常。')
        raise


    try:
        while True:
            input0 = input('enter: ')
            data = input0.encode('utf-8')

            udp_C.sendto(data, (addr, int(port)))
            if input0 == 'quit':
                break
            data, address = udp_C.recvfrom(1024)

            data = data.decode('utf-8')
            print(data)
    except:
        print('有发送异常。')
        raise

    finally:
        udp_C.close()