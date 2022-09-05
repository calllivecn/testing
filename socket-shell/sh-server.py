#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-04 04:14:14
# author calllivecn <c-all@qq.com>


import os
import sys
import pty
import fcntl
import struct
import termios
import asyncio
import argparse

from asyncio import (
    subprocess,
    streams,
    StreamReader,
    StreamWriter,
    StreamReaderProtocol,
)

from typing import (
    BinaryIO,
    Tuple,
)

SHELL="bash"

BUFSIZE = 1<<12 # 4K

STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()

def get_pty_size(fd):
    size = fcntl.ioctl(STDIN, termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(STDIN, termios.TIOCSWINSZ, size)


# 窗口大小调整
def signal_SIGWINCH_handle(sigNum, frame):
    size = get_pty_size(STDOUT)
    print(f"窗口大小改变: {size}")
    
    # termios.tcgetattr(sys.stdin)
    # termios.tcsetattr(sys.stdin, termios.TCSADRAIN, tty_bak)

    set_pty_size(STDOUT, *size)

    print("sigwinch 执行完成")



# async def waitproc(p: subprocess.Process) -> int:
async def waitproc(pty_slave: int) -> int:
    p = await subprocess.create_subprocess_exec(SHELL, stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid)
    recode = await p.wait()
    print(f"shell wait() done, recode: {recode}")
    os.close(pty_slave)
    return recode


async def connect_read_write(pty_master) -> Tuple[StreamReader, StreamWriter]:
    fileobj = open(pty_master)
    loop = asyncio.get_running_loop()

    reader = StreamReader()
    protocol = StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, fileobj)

    w_transport, w_protocol = await loop.connect_write_pipe(streams.FlowControlMixin, fileobj)
    writer = StreamWriter(w_transport, w_protocol, reader, loop)

    return reader, writer


async def relay(reader: StreamReader, writer: StreamWriter):
    print(f"relay start: {reader}")
    while (data := await reader.read(BUFSIZE)) != b"":
        print(reader, data)
        writer.write(data)
        await writer.drain()
    print(f"stream close()")




async def socketshell(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    env =  os.environ.copy()
    addr = writer.get_extra_info("peername")
    print(f"client {addr} connected.")

    pty_master, pty_slave = pty.openpty()
    pty_reader, pty_writer = await connect_read_write(pty_master)


    p_task = asyncio.create_task(waitproc(pty_slave))
    pty2sock = asyncio.create_task(relay(pty_reader, writer))
    sock2pty = asyncio.create_task(relay(reader, pty_writer))


    print("shell start")
    await p_task
    print("shell exit")

    writer.close()
    await writer.wait_closed()

    # 什么 pty_master 或者 pty_writer 不用close() ???
    # pty_writer.close()
    # await pty_writer.wait_closed()

    print("pty2sock start")
    pty2sock.cancel()
    print("pty2sock end")

    print("sock2pty start")
    sock2pty.cancel()
    print("sockpty end")

    results = await asyncio.gather(pty2sock, sock2pty, p_task, return_exceptions=True)
    print(f"gather() --> {results}")

    recode = p_task.result()
    print(f"client {addr} disconnect, recode: {recode}")


async def server(addr, port):
    sock = await asyncio.start_server(socketshell, addr, port, reuse_address=True)
    print(f"listent: {addr}, {port}")
    async with sock:
        await sock.serve_forever()


async def client(addr, port):
    reader, writer = await asyncio.open_connection(addr, port)



def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s <命令> [option]",
        description="远程shell连接",
        epilog="END",
    )

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    parse.add_argument("--addr", default="*", help="需要连接的IP或域名")
    parse.add_argument("--port", default=6789, type=int, help="端口")

    # parse.add_argument("--Spub", action="store", nargs="+", required=True, help="使用加密通信的对方公钥，server端可能有多个。")
    # parse.add_argument("--Spriv", action="store", required=True, help="使用加密通信的私钥。")

    subparsers = parse.add_subparsers(title="指令", metavar="")
    server_func =  subparsers.add_parser("server", help="启动服务端")
    client_func = subparsers.add_parser("client", help="使用client端")
    server_func.add_argument("--cmd", default=SHELL, help=f"需要使用的交互程序(default: {SHELL})")

    server_func.set_defaults(func=server)
    
    client_func.set_defaults(func=client)

    args = parse.parse_args()
    if args.parse:
        print(args)
        sys.exit(0)
    
    # if args.debug:
        # logger.setLevel(logging.DEBUG)
    

    asyncio.run(args.func(args.addr, args.port), debug=True)


if __name__ == "__main__":
    main()