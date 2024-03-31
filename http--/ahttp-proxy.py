#!/usr/bin/env python3
# coding=utf-8
# date 2021-03-09 15:26:026
# author calllivecn <calllivecn@outlook.com>


# import io
import ipaddress
import asyncio
import traceback
import logging
# from http import HTTPStatus
from argparse import ArgumentParser

from typing import (
    Union,
    Type,
)

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ModuleNotFoundError:
    pass


def getlogger():
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",datefmt="%Y-%m-%d-%H:%M:%S")
    handler.setFormatter(fmt)

    logger = logging.getLogger("http proxy")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


logger = getlogger()

class RequestError(Exception):
    pass

class MethodError(RequestError):
    pass

class HostPostError(RequestError):
    pass


class Buffer(bytearray):
    def __init__(self, size: int = 4096, mv: Union[memoryview, None] = None):
        self.size = size
        self.pos = 0

        if isinstance(mv, memoryview):
            super().__init__(mv)
            self._mv = mv
        else:
            super().__init__(size)
            self._mv = memoryview(self)
    
    def __getitem__(self, key: slice) -> Type["Buffer"]:
        buf = Buffer(key.stop, self._mv[key])
        return buf

    def __setitem__(self, slice_, data):
        self.pos = slice_.stop
        self._mv[slice_] = data
    
    def __len__(self):
        return self.pos
    
    def getvalue(self, start: int = 0, end: Union[int, None] = None) -> bytes:
        if end is None:
            return self._mv[start:self.pos].tobytes()
        else:
            return self._mv[start:end].tobytes()



class Header:

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        
        self._method = None
        # self.buffer = io.BytesIO()
        self.buffer = Buffer(8*(1<<10))
        self.buffer_pos = 0
        self.requestheaders = b""
        self.delimiter = 0
        self.body_start = b""

        self.host = None
        self.port = None

    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, value):
        self._method = value

    async def getRequest(self):

        while True:
            buffer = await self.reader.read(4096)

            if buffer == b"":
                raise RequestError("peer close connection")

            buffer_len = len(buffer)
            self.buffer[self.buffer.pos : self.buffer.pos + buffer_len] = buffer

            pos = self.buffer.find(b"\r\n\r\n", self.buffer_pos)

            logger.debug(f"{pos=}")

            if pos != -1:
                self.delimiter = pos
                break


            if self.buffer.pos >= 8192:
            # if self.buffer.tell() >= 8192:

                self.writer.write(b"HTTP/1.1 400 REQUEST TOO LONG")
                await self.writer.drain()
                self.writer.close()

                raise RequestError("request too long")


        try:
            logger.debug(f"self.buffer.decode() -->\n{self.buffer.getvalue().decode()}")
        except UnicodeDecodeError:
            logger.debug(f"self.buffer -->\n{self.buffer.getvalue()}")

        # 这里可以 把 request line 分离出来了
        self.headers = self.buffer.getvalue(0, self.delimiter+4).decode("utf8")

        logger.debug(f"self.headers ==>\n{self.headers}")

        self.method = self.headers[:self.headers.find(" ")]
    
    def isHttps(self):
        if self.method.upper() == "CONNECT":
            return True
        else:
            return False
            
    def data(self):
        # 跟在header 后面的部分数据
        if self.isHttps():
            data = self.buffer.getvalue(self.delimiter + 4)
        else:
            data = self.buffer.getvalue()

        logger.debug(f"请求头后面带着的部分数据：{data=}")
        return data
    
    def get_Host_Port(self):

        # 如果是https 否则是 http
        if self.isHttps():

            https_line = self.headers.split("\r\n")[0]
            logger.debug(f"https_line ==> {https_line}")

            method, host_port, protocol = https_line.split(" ")

            # CONNECT 下都会有默认端口的
            host, port = host_port.rsplit(":", 1)
            self.port = int(port)

            if host.startswith("[") and host.endswith("]"):
                self.host = host[1:-1]
            else:
                self.host = host

        else:

            for header in self.headers.split("\r\n"):
                key = header[:5].lower()

                if key == "host:":

                    host_value = header.split(":", 1)[1].split()[0]

                    # 检测是不是使用默认端口, 但是这里就要分为ipv4, ipv6, domain,  ipv6又要分带端口，和默认端口。
                    
                    # ipv6  带端口的
                    if host_value.find("]:") != -1:
                        host, port = host_value.rsplit(":", 1)
                        self.host = host[1:-1]
                        self.port = int(port)

                    # ipv6 默认端口的
                    elif host_value.find("]") != -1:
                        self.host = host_value[1:-1]
                        self.port = 80

                    # ipv4 和 domain 不使用在细分了
                    elif host_value.find(":") != -1:
                        self.host, port = host_value.rsplit(":", 1)
                        self.port = int(port)
                    else:
                        self.host = host_value
                        self.port = 80
                    
                    break


            else:
                logger.warning("host: port 解析错误。")
                raise HostPostError("host: port 解析错误。")
            
        logger.debug(f"target addr --> {self.host=} {self.port=}")
        if self.host is None or self.port is None:
            raise RequestError("没有解析到host port")
        


async def swap(r1, w2):
    logger.debug(f"id: {id(r1)}")

    try:
        while True:
            data = await asyncio.wait_for(r1.read(4096), timeout=TIMEOUT)

            if not data:
                break

            i = w2.write(data)
            await asyncio.wait_for(w2.drain(), timeout=TIMEOUT)

    except ConnectionResetError as e:
        logger.debug(f"{e}")
    
    except asyncio.TimeoutError:
        logger.warning(f"data swap Timeout close()")

    finally:
        w2.close()
        await w2.wait_closed()


async def handle_add_timeout(reader, writer):
    addr = writer.get_extra_info("peername")

    head = Header(reader, writer)
    await asyncio.wait_for(head.getRequest(), timeout=TIMEOUT)
    head.get_Host_Port()

    r2, w2 = await asyncio.wait_for(asyncio.open_connection(head.host, head.port, limit=4096), timeout=TIMEOUT)

    if head.isHttps():
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        # await writer.drain()
        await asyncio.wait_for(w2.drain(), timeout=TIMEOUT)
    else:
        w2.write(head.data())
        # await writer.drain()
        await asyncio.wait_for(w2.drain(), timeout=TIMEOUT)

    # 我去， 这里必需是分开的 task 不然不是并发的....
    task1 = asyncio.create_task(swap(reader, w2))
    task2 = asyncio.create_task(swap(r2, writer))
    await task1 
    await task2 


async def handle(reader, writer):
    addr = writer.get_extra_info("peername")

    try:
        await handle_add_timeout(reader, writer)
    except asyncio.TimeoutError:
        logger.debug(f"{addr} Timeout close()")

    except OSError as e:
        logger.warning(e)

    except Exception as e:
        # logger.warning(f"异常：{e}")
        traceback.print_exception(e)
    
    finally:
        writer.close()
        await writer.wait_closed()

async def proxy():
    parse = ArgumentParser(
        description="一个用asyncio实现的http https代理服务器。",
        usage="%(prog)s [ --addr <0.0.0.0>|<::> <*>] [--port <8080>]",
        epilog="calllivecn 编写"
    )

    parse.add_argument("--addr", default="*", help="指定监听地址，默认同时监听ipv4 ipv6")
    parse.add_argument("--port", type=int, default=8080, help="指定监听端口default: 8080")
    parse.add_argument("--debug", action="store_true", help="--debug")

    args = parse.parse_args()

    if args.debug:
        print(args)
        # sys.exit(0)
    else:
        logger.setLevel(logging.INFO)

    sock_server = await asyncio.start_server(handle, args.addr, args.port, limit=4096, reuse_address=True, reuse_port=True)

    # addr, port = sock_server.sockets[0].getsockname()
    print("listen:", args.addr, "port:", args.port)

    async with sock_server:
        await sock_server.serve_forever()


TIMEOUT=600

try:
    asyncio.run(proxy())
except KeyboardInterrupt:
    pass
