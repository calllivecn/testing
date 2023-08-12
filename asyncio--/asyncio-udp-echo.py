#!/usr/bin/env python3
# coding=utf-8
# date 2023-08-06 13:47:00
# author calllivecn <c-all@qq.com>



import time
import socket
import asyncio

from typing import (
    Any,
)


"""
官方文档里的示例
"""

import asyncio

class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        print('Send %r to %s' % (message, addr))
        self.transport.sendto(data, addr)


async def server():
    print("Starting UDP server")

    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    # One protocol instance will be created to serve all
    # client requests.
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=('127.0.0.1', 9999))

    try:
        await asyncio.sleep(3600)  # Serve for 1 hour.
    finally:
        transport.close()


class EchoClientProtocol:
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        print("Received:", data.decode())

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")
        self.on_con_lost.set_result(True)


async def client():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = "Hello World!"

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(message, on_con_lost),
        remote_addr=('::', 9999))

    try:
        await on_con_lost
    finally:
        transport.close()


# asyncio.run(client());exit(0)

"""
end 
"""

class UDPEchoServerProtocol(asyncio.DatagramProtocol):

    count = 0

    def connection_made(self, transport):
        self.transport = transport
        self.sock = transport.get_extra_info("socket")

        UDPEchoServerProtocol.count += 1
        print("这是在什么阶段执行的？")

    def datagram_received(self, data, addr):
        print(f"{self.count=} {addr=}: {data=}")
        self.transport.sendto(data, addr)
    

    def connection_lost(self, exc: Exception | None) -> None:
        print("这个UDP socket close()")



def server():
    loop = asyncio.get_event_loop()
    print("Starting UDP server")
    # One protocol instance will be created to serve all client requests
    listen = loop.create_datagram_endpoint(UDPEchoServerProtocol, local_addr=('0.0.0.0', 9999))
    transport, protocol = loop.run_until_complete(listen)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    transport.close()
    loop.close()


async def server2():
    loop = asyncio.get_running_loop()
    print("Starting UDP server")
    transport, protocol = await loop.create_datagram_endpoint(UDPEchoServerProtocol, local_addr=("::", 9999))

    # print(f"{type(transport)=}\n{dir(transport)=}\n{type(protocol)=}")

    future = loop.create_future()
    try:
        # await asyncio.sleep(3600) # 这样是可以，但是怎么让它 while True：起来呢？
        # while True:
        #   await asyncio.sleep(60)
            await future # 这样才对嘛
    except KeyboardInterrupt:
        future.cancel()
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        transport.close()
        loop.stop()
        loop.close()


QPair = Any
class UDPServer3:
    """
    这种方式要在py3.11及以上才行, 以下的只能使用 loop.sock_recv(), loop.sock_send() 的 TCP 的方法。
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setblocking(False)
        self.loop = asyncio.get_running_loop()

        self.buf = memoryview(bytearray(8*(1<<20)))
        self.buf_n = 0

    def accept(self, host, port) -> QPair:
        self.sock.bind((host, port))

        self.buf_n = self.loop.sock(self.sock, self.buf)

        self.loop.sock_sendall

    
    def connect(self, host, port):
        pass


# asyncio.run(server())
asyncio.run(server2(), debug=True)
