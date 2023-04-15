"""
在 reuseport 和 selectors 之下， ab 是性能瓶颈了～～～ 😂
"""

import selectors
import socket
import sys

#import multiprocessing as mproc

def httpResponse(msg):
    response = [
            "HTTP/1.1 200 ok",
            "Server: py",
            "Content-Type: text/plain",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    return "\r\n".join(response).encode("utf8") + msg



def accept(sock, mask, sel):
    conn, addr = sock.accept()
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)


def close(sock, mask, sel):
    sel.unregister(sock)
    sock.close()

def write(sock, mask, sel):
    sock.send(httpResponse(b"hello world!\n"))
    sel.modify(sock, selectors.EVENT_WRITE, close)


def read(sock, mask, sel):
    try:
        data = sock.recv(1024)
    except ConnectionResetError:
        sock.close()
        sel.unregister(sock)
        return

    #print("read():", data)
    # send http response
    sel.modify(sock, selectors.EVENT_WRITE, write)



ADDR = ('0.0.0.0', 6784)
def process():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
    sock.bind(ADDR)
    sock.listen(128)
    sock.setblocking(False)

    sel = selectors.DefaultSelector()
    sel.register(sock, selectors.EVENT_READ, accept)

    while True:

        for key, mask in sel.select():
            callback = key.data
            callback(key.fileobj, mask, sel)


print("listen: ", ADDR)
# 使用单进程 好用 cProfile 分析性能
process()

"""
process_list = []
for _ in range(2):
    p = mproc.Process(target=process, daemon=True)
    p.start()
    process_list.append(p)

try:

    for proc in process_list:
        proc.join()

except KeyboardInterrupt:
    print("exit")
"""
