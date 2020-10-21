"""
在 reuseport 和 selectors 之下， ab 是性能瓶颈了～～～ 😂
"""

import selectors
import socket
import time

import multiprocessing as mproc

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

def read(conn, mask, sel):
    data = conn.recv(1024)
    #print("read():", data)
    # send http response
    conn.send(httpResponse(b"hello world!\n"))
    sel.unregister(conn)
    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()


ADDR = ('0.0.0.0', 6784)
def process():
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
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
