#!/usr/bin/env python3
# coding=utf-8
# date 2023-07-31 03:22:28
# author calllivecn <c-all@qq.com>



import sys
import socket
import struct

IF_INDEX = int(sys.argv[2])
MCAST = "ff12::1234"
PORT = 6789

def server():
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    sock.bind(('::', PORT))

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, IF_INDEX)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)

    # 加入组播地址 MCAST
    mreq = struct.pack("16sI", socket.inet_pton(socket.AF_INET6, MCAST), IF_INDEX)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    data, addr = sock.recvfrom(1024)

    print(f"addr: {addr} data: {data}")

    sock.sendto(b"ok", addr)

    sock.close()

def client():
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, IF_INDEX)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 1)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_LOOP, 1)

    # mreq = struct.pack("16s15s", socket.inet_pton(socket.AF_INET6, MCAST), bytes(16))
    mreq = struct.pack("16sI", socket.inet_pton(socket.AF_INET6, MCAST), IF_INDEX)
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)


    sock.sendto(b"calllivecn ten test", (MCAST, PORT))

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