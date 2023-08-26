#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-11 21:09:12
# author calllivecn <c-all@qq.com>


import socket
import selectors


def main(wg_ipv4="127.0.0.1", wg_ipv6="::1", CHECK_PORT=6789):

    se = selectors.DefaultSelector()
    socks = []
    if wg_ipv4 is not None:
        sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock4.bind((wg_ipv4, CHECK_PORT))
        se.register(sock4, selectors.EVENT_READ)
        socks.append(sock4)


    sock6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock6.bind((wg_ipv6, CHECK_PORT))

    se.register(sock6, selectors.EVENT_READ)
    socks.append(sock6)

    while True:
        for key, event in se.select():
            data, addr = key.fileobj.recvfrom(8192)
            print(f"{addr} {data=}")
    
    for sock in socks:
        sock.close()

    se.close()
            

if __name__ == "__main__":
    main()