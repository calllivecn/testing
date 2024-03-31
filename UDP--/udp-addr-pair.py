#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-09 12:50:33
# author calllivecn <calllivecn@outlook.com>


import sys
import asyncio
import logging
from asyncio import (
    DatagramTransport,
)

from typing import (
    Any,
    Tuple,
    Dict,
    Union,
    Type,
    TypeVar,
)

def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)

    logger = logging.getLogger("test")

    logger.setLevel(level)
    logger.addHandler(stream)
    return logger


logger = getlogger(logging.DEBUG)




class QPair:

    def __init__(self, size=500) -> None:
        self.r = asyncio.Queue(size)
        self.w = asyncio.Queue(size)
    

AddrTuple = TypeVar("AddrTuple", str, Any, int) # 这是af_inet 的

DataBuf = TypeVar("DataBuf", bytes, bytearray, memoryview)



class _BaseAUDP(asyncio.DatagramProtocol):

    def __init__(self, recv_queue) -> None:
        super().__init__()

        self.q = recv_queue
    

    def connection_made(self, transport: DatagramTransport) -> None:
        self.tp = transport
    
    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        logger.debug(f"收到底层UDP包: {addr=} --> {data}")
        try:
            self.q.put_nowait((data, addr))
        except asyncio.QueueFull:
            logger.debug(f"队列满, 丢弃数据包: {data=}")

    def connection_lost(self, exc: Exception | None) -> None:
        pass


class UDPPair:

    def __init__(self, transport, peer: AddrTuple, pair: asyncio.Queue):
        self.transport = transport
        self.peer = peer
        self.pair = pair


    async def udp_recv(self, nbytes: int) -> bytes:
        return await self.pair.get()
    

    def udp_send(self, data: DataBuf):
        self.transport.sendto(data, self.peer)

    async def close(self):
        pass


class AUDPServer:

    def __init__(self, sock=None):

        self.peers: Dict[AddrTuple, QPair] = {}

        self._is_accept  = False
        self._q_accept = asyncio.Queue(5)

        self._is_connect = False

        self._loop = asyncio.get_running_loop()
        self._sock = sock

        self._base_q = asyncio.Queue()
        self._base_q_size = 8*(1<<20)


        self.tasks = []
        # 并行发任务
        self.tasks.append(asyncio.create_task(self._recvform()))


    async def accept(self, listenaddr: AddrTuple) -> UDPPair:
        if not self._is_accept:
            await self._init_accept(listenaddr)

        return await self._q_accept.get()
    

    async def connect(self, addr: AddrTuple):
        self._init_connect(addr)

    
    async def sendto(self, data: DataBuf, addr: AddrTuple):
        await self.tp.sendto(data, addr)

    async def _recvform(self) -> (DataBuf, AddrTuple):

        while True:

            data, addr = await self._base_q.get()
            peer = self.peers.get(addr)

            if peer is None:
                await self._new_peer(data, addr)
            else:
                qpair = self.peers[addr]
                # await qpair.w.put(data)
                await qpair.put(data)


    async def close(self):
        self.tp.close()

        for task in self.tasks:
            task.cancel()


    async def _init_accept(self, laddr: AddrTuple):
        self._is_accept = True
        transport, protocol = await self._loop.create_datagram_endpoint(lambda: _BaseAUDP(self._base_q), local_addr=laddr)
        self.tp = transport


    async def _init_connect(self, peer_addr: AddrTuple):
        self._is_connect = True
        transport, protocol = await self._loop.create_datagram_endpoint(lambda: _BaseAUDP(self._base_q), remote_addr=peer_addr)
        self.tp = transport


    async def _new_peer(self, data: DataBuf, addr: AddrTuple):
        # qpair = QPair()
        qpair = asyncio.Queue(100)
        self.peers[addr] = qpair
        await qpair.put(data)

        await self._q_accept.put(UDPPair(self.tp, addr, qpair))
   


async def clienthandle(pair: UDPPair):


    while True:
        data = await pair.udp_recv(8192)
        logger.debug(f"这是一个对端: {pair.peer}")
        pair.udp_send(f"你的地址: {pair.peer}".encode() + data)


async def server():
    server = AUDPServer()

    while True:
        con = await server.accept(("::", 6789))
        logger.debug(f"新的客户端：{con.peer}")

        # 开起一个新的并发
        asyncio.create_task(clienthandle(con))


        
try:
    asyncio.run(server(), debug=True)
except KeyboardInterrupt:
    pass