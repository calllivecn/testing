"""
线程池也很快， 12k。
"""

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



def process(pool=10):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
    sock.bind(ADDR)
    sock.listen(1024)

    pool = ThreadPoolExecutor(pool)

    while True:
        client, addr = sock.accept()
        pool.submit(echo, client)


ADDR = ('0.0.0.0', 6786)
Pool = 10

print("listen: ", ADDR, "Thread: ", Pool)
try:
    process(Pool)
except KeyboardInterrupt:
    print("exit")
