#!/usr/bin/env python3
# coding=utf-8
# date 2022-05-14 08:39:33
# author calllivecn <c-all@qq.com>


# 先尝试稳定传输

"""
需要设计数据包格式
"""

import time
import queue
import socket
import struct
import selectors

from threading import (
    Thread,
    Lock,
)

packet_version = 0x01

# from logs import logger

class logger:

    def debug(self, msg):
        print(time.localtime(), msg)

    def info(self, msg):
        print(time.localtime(), msg)


class Buffer(bytearray):
    def __init__(self, size: int=4096):

        super().__init__(size)
        # self._ba = bytearray(size)
        self._mv = memoryview(self)
    
    def __getitem__(self, slice: slice):
        return self._mv[slice]


class PacketError(Exception):
    pass

class Packet:

    def __init__(self):
        self.version = struct.pack("!H", packet_version) # 2byte
        self.seq = bytes(8) # 8byte
        # self.clientid = bytes(8) # 8byte, 服务端需要看看，怎么高效的分配client id; 不需要，直接使用ip+port对的方式, 不过需要在Server, 内部标识。
        self.ctl = bytes(2) # type 字段，初始化 packet 时为0
        # ctl： 包类型，如：SYN, ACK, FIN, RESET, DAT(连接后的数据传输类型),  NACK(另端主动要 ACK)
        self.payload = bytes(2) # 2bytes, UDP的负载大小。(实际还有PMTU有关，需要实测。)

        self.proto = struct.Struct("!HQQHH")

        self.MAX_PAYLOAD = 65535 - self.proto.size

    def frombuf(self, data: bytes):
        ( 
            self.version, 
            self.seq,  
            # self.clientid,
            self.ctl,
            self.payload,
        ) = self.proto.unpack(data[:self.proto.size])

    def tobuf(self, data: bytes):

        self.payload = len(data)

        if self.payload >= self.MAX_PAYLOAD:
            raise PacketError("payload too long")

        self.seq += 1
        header = self.pack(
            self.version,
            self.seq,
            # self.clientid,
            self.ctl, 
            self.payload
            )

        return header + data



class TranterStatusError(Exception):
    pass

class Tranter:
    """
    这个就是对上层提供的服务类？time:2022-05-15 
    """

    def listen(self, size: int):
        """
        队列大小, 也可以不调用这步，默认值为128
        """
        self._accept_queue = queue.Queue(size)

    def bind(self, addr: str, port: int):
        self.addr = addr
        self.port = port

        self.sock.bind((self.addr, self.port))

    
    def accept(self):
        """
        这个是需要等client新建连接
        """
        # 启动接收队列
        if self._accept_queue.locked():
            self._accept_queue.release()
        # else:
            # raise TranterStatusError("")

        
        # 连接成功建立时，对端的地址信息
        sock = self._rx.get()
        return sock
    
    def connect(self, addr: str, port: int):
        """
        client(主动连接方)
        这里需要保存的状态：clientID, _stat(连接状态)
        """
        self._clientid = self._connect(addr, port)

    def recv(self, size: int):
        """
        这个对上层应该是流式传输。
        """
        return self._rx.get()


    def send(self, data: bytes):
        """
        这个对上层应该是流式传输。
        """
        addr_info = self._ids[self._clientid]
        self.sock.sendto(data, addr_info)


    """
    这是tranter内部实现
    """
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self._buf = Buffer(1<<16) # 默认64K

        # TCP的状态，传输层的状态？
        self._stat = 1

        self._closed = False

        # 当前已建立连接的 clientID: map 到对方的(addr 无组)
        # 怎么分配 8 字节的ID？
        self._ids = {}

        # 当是 client 需要保留的信息


        # event 方式
        self.selector = selectors.DefaultSelector()

        # 使用队列，向上层交付 recv() send() 功能
        self._rx = queue.Queue(128)
        self._tx = queue.Queue(128)
        
        # listen(128) 和默认值
        self._accept_queue = queue.Queue(128)

        self._accept_lock = Lock()
        self._accept_lock.acquire()

        self._lock_recv = Lock()
        self._lock_recv.acquire()

        # 还需要用到线程才行
        self.rt_loop = Thread(target=self._tranter, daemon=True)
        self.rt_loop.start()
    
    def _recv(self):
        """
        Q: 这里，和send 使用的是同一个，sock 怎么为上层提供阻塞的 socket的: recv() send() 功能？
        A1: 使用 event ?, socketors, 可以试试。需要自己设计一个事件循环！
        R1: 这个感觉行不通

        A2: 使用队列？
        """

        self._offset, self._address = self.sock.recvfrom_into(self._buf, size)
        data, addr = self.sock.recvfrom_into(self._buf)

        if len(data) < self.proto.size:
            logger.debug(f"从 {addr} 接收到无效大小的包.")
            return "需要有个recode"
        
        # 检查，包大小和payload 对不对

        self.selector.register(self.sock, selectors.EVENT_READ)

        data, addr = self.sock.recvfrom_into(self._buf)

        # 这里需要处理 packet 类型


    def _connect(self):
        pass