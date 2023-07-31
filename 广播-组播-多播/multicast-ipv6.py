#!/usr/bin/env python3
# coding=utf-8
# date 2022-03-15 07:34:58
# author calllivecn <c-all@qq.com>



import sys
import socket
import struct


def server():
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Allows address to be reused

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Binds to all interfaces on the given port

    sock.bind(('', 8080))

    # Allow messages from this socket to loop back for development

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)

    # Construct message for joining multicast group

    # mreq = struct.pack("16s15s".encode('utf-8'), socket.inet_pton(socket.AF_INET6, "ff02::abcd:1"), (chr(0) * 16).encode('utf-8'))

    # sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    data, addr = sock.recvfrom(1024)

    print(f"addr: {addr} data: {data}")

    sock.sendto(b"ok", addr)

    sock.close()

def client():
    # Create ipv6 datagram socket
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    # Allow own messages to be sent back (for local testing)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, True)

    # sock.sendto("hello world".encode('utf-8'), ("ff02::abcd:1", 8080))
    sock.sendto("hello world".encode('utf-8'), ("ff02::1", 8080))

    data, addr = sock.recvfrom(1024)

    print(f"收到 {addr} 回复： {data}")

    sock.close()

if __name__ == "__main__":
    if sys.argv[1] == "client":
        client()
    elif sys.argv[1]== "server":
        server()
    else:
        print("????? 使法不对。")