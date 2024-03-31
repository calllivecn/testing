#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-01 05:35:32
# author calllivecn <calllivecn@outlook.com>


import sys
import socket
import struct
import binascii


def test1():
    # 创建一个socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    # 设置TTL
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 10)

    # 发送ICMP Echo Request数据包
    # sock.sendto(b'\x08\x00\x00\x00\x00\x00\x00\x00', ('www.tmall.com', 80))
    sock.sendto(b'\x08\x00\x00\x00\x00\x00\x00\x00', ('192.168.8.10', 80))

    # 接收ICMP Echo Reply数据包
    data, address = sock.recvfrom(1024)
    data = binascii.b2a_hex(data)

    # 打印ICMP Echo Reply数据包 print(f"{address=} -> {data=}")



# 测试ok
def checksum(packet: bytes) -> int:
    """
    计算ICMP数据包的校验和。
  
    Args:
      packet: ICMP数据包。
  
    Returns:
      ICMP数据包的校验和。
    """
    sum = 0
    for i in range(0, len(packet), 2):
        sum += int.from_bytes(packet[i:i + 2], "big")
    
    sum = (sum & 0xffff) + (sum >> 16)
    sum = ~sum & 0xffff

    return sum


def send_icmp_packet(ip_address):
    # 构建ICMP数据包
    packet_id = 1
    packet_seq = 1
    packet_data = b'Hello World!.'

    # 构建ICMP头部
    icmp_type = 8  # ICMP Echo Request
    icmp_code = 0
    icmp_checksum = 0

    # 计算ICMP头部校验和
    icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, packet_id, packet_seq) + packet_data

    icmp_checksum = checksum(icmp_header)

    # print(f"{icmp_checksum=}")

    # 构建完整的ICMP数据包
    packet = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, packet_id, packet_seq) + packet_data

    # 创建socket并发送数据包
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    print(f"发送数据: {packet=}")
    sock.sendto(packet, (ip_address, 0))
    redata, addr = sock.recvfrom(8192)
    print(f"{redata=}")

    sock.close()


if __name__ == "__main__":
    send_icmp_packet(sys.argv[1])
