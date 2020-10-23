"""
线程池也很快， 12k。
"""

import queue
import socket
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

def httpResponse(msg):
    response = [
            "HTTP/1.1 200 ok",
            "Server: py",
            "Content-Type: text/plain",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    return "\r\n".join(response).encode("utf8") + msg


def echo(conn):
    try:
        data = conn.recv(1024)
        if not data:
            return
        # send http response
        conn.send(httpResponse(b"hello world!\n"))
    except Exception as e:
        print("异常：", e)
    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()



def thread1(pool=10):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
    sock.bind(ADDR)
    sock.listen(1024)

    pool = ThreadPoolExecutor(pool)

    while True:
        client, addr = sock.accept()
        pool.submit(echo, client)


class ThreadPool:

    def __init__(self, func, threads=10):
        self.pools = []
        self.q = queue.Queue(512)

        for th in range(threads):
            th = Thread(target=self.__proc, daemon=True)
            th.start()
            self.pools.append(th)

    def submit(self, func, *args, **kwargs):
        self.q.put((func, args, kwargs))

    def join(self):
        for th in self.pools:
            th.join()
        
    def __proc(self):
        while True:
            func, args, kwargs = self.q.get()
            # 这里不需要 result
            result = func(*args, **kwargs)


def thread2(pool=10):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)

    sock.bind(ADDR)
    sock.listen(1024)

    pool = ThreadPool(10)

    while True:
        client, addr = sock.accept()
        pool.submit(echo, client)


ADDR = ('0.0.0.0', 6786)
Pool = 10

print("listen: ", ADDR, "Thread: ", Pool)
try:
    #thread1(Pool)
    thread2(Pool)
except KeyboardInterrupt:
    print("exit")
