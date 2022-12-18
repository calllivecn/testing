#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-16 01:00:47
# author calllivecn <c-all@qq.com>


import sys
import socket
from selectors import (
    DefaultSelector,
    EVENT_READ,
    EVENT_WRITE,
)


def server(addr="", port=6789):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind((addr, port))

    se = DefaultSelector()

    se.register(sock, EVENT_READ)

    buf = memoryview(bytearray(10*(1<<10)))

    CONT = True
    while CONT:
        for sockkey, event in se.select():
            if event == EVENT_READ:
                n, addr = sock.recvfrom_into(buf)
                sock.sendto(buf[:n], addr)

                if buf[:5].tobytes() == b".exit":
                    print("server exit.")
                    CONT = False
                    break

                print(f"接收到：{addr} --> {buf[:n].tobytes()}")
    
    sock.close()
    se.close()



def client(addr, port=6789):
    target = (addr, port)
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    while True:
        text = input("输入：")
        sock.sendto(text.encode(), target)
        replay = sock.recvfrom(1024)
        if text == ".exit":
            break

        print(f"回复: {replay}")
    
    sock.close()




if __name__ == "__main__":
    if sys.argv[1] == "server":
        server("", int(sys.argv[2]))
    elif sys.argv[1] == "client":
        client(sys.argv[2], int(sys.argv[3]))
    else:
        print("查看源码使用")
