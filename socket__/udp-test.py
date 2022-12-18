#!/usr/bin/env python3
# coding=utf-8

import sys
import time
import socket

buf = 1024


def server(addr="", port=6789):

    BIND = (addr, port)

    try:
        udp_S = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_S.bind(BIND)
        # udp_S.settimeout(30)
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



def client(addr, port):

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

if __name__ == "__main__":
    if sys.argv[1] == "server":
        server(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1] == "client":
        client(sys.argv[2], int(sys.argv[3]))
    
    else:
        print("用法查看源码")