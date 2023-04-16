#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-04 04:14:14
# author calllivecn <c-all@qq.com>


import os
import sys
import tty
import pty
import fcntl
import struct
import socket
import termios
import asyncio
import logging
import argparse
import threading
import multiprocessing as mprocess

from asyncio import (
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


def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger = logging.getLogger("sh-server")
    logger.setLevel(level)
    logger.addHandler(stream)
    return logger


logger = getlogger()



def get_pty_size(fd):
    size = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


# 窗口大小调整, 这样是调控制端的。 暂时先不支持。
def signal_SIGWINCH_handle(sock, sigNum, frame):
    """
    usage: lambda sigNum, frame: signal_SIGWINCH_handle(sock, sigNum, frame)
    """
    size = get_pty_size(fd)
    # logging 在异步的信号量模式下不安全。在 signal handle 里不要用 logging
    # logger.debug(f"窗口大小改变: {size}")
    # logger.debug("sigwinch 向对端发送新窗口大小")
    # set_pty_size(STDOUT, *size)
    sock.write(PacketType.TTY_RESIZE, struct.pack("!HH", *size))


async def waitproc(shell: str, pty_slave: int) -> int:
    # p = await subprocess.create_subprocess_exec(shell, stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid)
    p = await asyncio.create_subprocess_exec(shell, stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid)
    recode = await p.wait()
    logger.debug(f"shell wait() done, recode: {recode}")
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
    logger.debug(f"relay: {reader} --> {writer}")
    while (data := await reader.read(BUFSIZE)) != b"":
        writer.write(data)
        await writer.drain()
    logger.debug(f"stream close()")


async def connect_to_socket(socket):
    reader, writer = await asyncio.open_connection(sock=socket)
    return reader, writer


# async def socketshell(shell: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
async def socketshell(shell: str, client: socket.SocketType):

    reader, writer = await connect_to_socket(client)

    addr = writer.get_extra_info("peername")
    logger.info(f"client {addr} connected.")

    pty_master, pty_slave = pty.openpty()
    pty_reader, pty_writer = await connect_read_write(pty_master)


    p_task = asyncio.create_task(waitproc(shell, pty_slave))
    pty2sock = asyncio.create_task(relay(pty_reader, writer))
    sock2pty = asyncio.create_task(relay(reader, pty_writer))


    logger.debug("shell start")
    await p_task
    logger.debug("shell exit")

    writer.close()
    await writer.wait_closed()

    # 什么 pty_master 或者 pty_writer 不用close() ???
    # 目前看应该是 connect_read_write() 自动关闭的。
    # pty_writer.close()
    # await pty_writer.wait_closed()

    logger.debug("pty2sock start")
    pty2sock.cancel()
    logger.debug("pty2sock end")

    logger.debug("sock2pty start")
    sock2pty.cancel()
    logger.debug("sockpty end")

    results = await asyncio.gather(pty2sock, sock2pty, p_task, return_exceptions=True)
    logger.debug(f"gather() --> {results}")

    recode = p_task.result()
    logger.info(f"client {addr} disconnect, recode: {recode}")


# 为登录的shell开一个子进程，这样不行。不能直接启动协程
def start_shell(shell, client):
    p = mprocess.Process(target=lambda: asyncio.run(socketshell(shell, client)))
    p.start()

    # 传给子进程后，在父进程需要关闭。
    client.close()
    
    p.join()
    logger.debug(f"子进程 {p.pid} shell退出.")



async def server(args):
    sock = await asyncio.start_server(lambda r, w: socketshell(args.cmd, r, w), args.addr, args.port, reuse_address=True)
    logger.info(f"listent: {args.addr}, {args.port}")
    async with sock:
        await sock.serve_forever()



# 2023-04-16 使用多进程开启子进程
def server_process(args):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.addr, args.port))
    sock.listen(128)

    logger.info(f"listen: {args.addr} port:{args.port}")

    try:
        while True:
            client, addr = sock.accept()
            # start_shell(args.cmd, client)
            th = threading.Thread(target=start_shell, args=(args.cmd, client))
            th.start()

    # 不能使用CTRL+C这样已经登录的子进程也会被干掉。
    except KeyboardInterrupt:
        pass


async def client(args):

    # 这两个只在client 使用
    STDIN = sys.stdin.fileno()
    STDOUT = sys.stdout.fileno()

    reader, writer = await asyncio.open_connection(args.addr, args.port)

    tty_bak = termios.tcgetattr(STDIN)
    tty.setraw(STDIN)
    
    loop = asyncio.get_running_loop()

    stdiner = StreamReader()
    protocol = StreamReaderProtocol(stdiner)
    r_transport, r_protocol = await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    w_transport, w_protocol = await loop.connect_write_pipe(streams.FlowControlMixin, sys.stdout)
    stdouter = StreamWriter(w_transport, w_protocol, stdiner, loop)

    stdin2sock = asyncio.create_task(relay(stdiner, writer))
    sock2stdout = asyncio.create_task(relay(reader, stdouter))

    await sock2stdout
    await sock2stdout
    stdin2sock.cancel()
    sock2stdout.cancel()

    writer.close()
    await writer.wait_closed()

    termios.tcsetattr(STDIN, termios.TCSADRAIN, tty_bak)
    logger.debug("restore termios")



def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s <命令> [option]",
        description="远程shell连接",
        epilog="END",
    )

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)
    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    parse.add_argument("--addr", default="::", help="需要连接的IP或域名")
    parse.add_argument("--port", default=6789, type=int, help="端口(default: 6789")

    # parse.add_argument("--Spub", action="store", nargs="+", required=True, help="使用加密通信的对方公钥，server端可能有多个。")
    # parse.add_argument("--Spriv", action="store", required=True, help="使用加密通信的私钥。")

    subparsers = parse.add_subparsers(title="指令", metavar="")
    server_func =  subparsers.add_parser("server", help="启动服务端")
    client_func = subparsers.add_parser("client", help="使用client端")
    server_func.add_argument("--cmd", default=SHELL, help=f"需要使用的交互程序(default: {SHELL})")

    # server_func.set_defaults(func=server)
    server_func.set_defaults(func=server_process)
    
    client_func.set_defaults(func=client)

    args = parse.parse_args()
    if args.parse:
        print(args)
        sys.exit(0)
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    
    if args.func is server_process:
        args.func(args)

    elif args.func is client:
        # asyncio.run(args.func(args.addr, args.port), debug=True)
        asyncio.run(args.func(args))

    else:
        logger.critical(f"？？？")
        sys.exit(1)


if __name__ == "__main__":
    main()