#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-28 13:44:14
# author calllivecn <c-all@qq.com>

import socket
import time

class ReliableUDP:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        self.sock.settimeout(1)

        # 初始化序列号和确认号
        self.seq_num = 0
        self.ack_num = 0

        # 初始化拥塞窗口大小和慢启动阈值
        self.cwnd = 1
        self.ssthresh = 16

        # 初始化拥塞控制参数
        self.alpha = 0.8
        self.beta = 0.25

    def send(self, data):
        # 发送数据包
        packet = str(self.seq_num) + ":" + data
        self.sock.sendto(packet.encode(), (self.ip, self.port))

        # 等待确认
        while True:
            try:
                ack_packet, addr = self.sock.recvfrom(1024)
                ack_num = int(ack_packet.decode())
                if ack_num == self.seq_num:
                    break
            except socket.timeout:
                print("Timeout! Resending packet...")
                self.sock.sendto(packet.encode(), (self.ip, self.port))

                # 拥塞窗口减半，慢启动阈值减半
                self.ssthresh = max(self.cwnd // 2, 1)
                self.cwnd = 1

        # 更新拥塞窗口大小
        if self.cwnd < self.ssthresh:
            # 慢启动阶段，指数增长
            self.cwnd *= 2
        else:
            # 拥塞避免阶段，线性增长
            self.cwnd += int(self.alpha * (self.cwnd ** 2) / (self.cwnd + 1))

        # 更新序列号
        self.seq_num += 1

    def receive(self):
        while True:
            try:
                packet, addr = self.sock.recvfrom(1024)
                seq_num, data = packet.decode().split(":")
                if int(seq_num) == self.ack_num:
                    ack_packet = str(self.ack_num)
                    self.sock.sendto(ack_packet.encode(), (self.ip, self.port))

                    # 更新确认号
                    self.ack_num += 1

                    # 更新拥塞窗口大小
                    if random.random() < self.beta:
                        # 拥塞避免阶段，线性减小
                        self.cwnd -= int(self.alpha * (self.cwnd ** 2) / (self.cwnd + 1))

                    return data
            except ValueError:
                pass

if __name__ == "__main__":
    import random
    server_ip = "127.0.0.1"
    server_port = 12345
    client_ip = "127.0.0.1"
    client_port = random.randint(10000, 20000)

    server = ReliableUDP(server_ip, server_port)
    client = ReliableUDP(client_ip, client_port)

    client.send("Hello world!")
    print(server.receive())
