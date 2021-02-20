#!/usr/bin/env python3
#coding=utf-8

import time
import socket
import selectors

def httpResponse(msg):
    response = [
            "HTTP/1.1 200 ok",
            "Server: server",
            "Content-Type: text/plain",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    data = "\r\n".join(response) + msg
    return data.encode("utf8")

def send_handler(conn, selector):
    ip = conn.getpeername()[0]
    conn.send(httpResponse(ip))
    conn.close()
    selector.unregister(conn)

def recv_handler(conn, selector):
    r = conn.recv(4096)
    # selector.register(conn, selectors.EVENT_WRITE, send_handler)
    selector.modify(conn, selectors.EVENT_WRITE, send_handler)

    # ip = conn.getpeername()[0]
    # print("client：", ip)
    # conn.send(httpResponse(ip))
    # conn.close()
    # selector.unregister(conn)


def handler_accept(conn, selector):
    sock , addr = conn.accept()
    sock.setblocking(False)
    selector.register(sock, selectors.EVENT_READ, recv_handler)

def server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    listener.setblocking(False)
    listener.bind((host, port))
    listener.listen(128)

    selector = selectors.DefaultSelector()
    selector.register(listener, selectors.EVENT_READ, handler_accept)

    task_count = 0
    start = time.time()
    try:
        while True:
            for key, event in selector.select():

                conn = key.fileobj
                func = key.data
                func(conn, selector)

                task_count += 1
                end = time.time()
                if (end - start) >= 1:
                    task = task_count
                    task_count = 0
                    print("当前处理连接数：{}/s".format(task))
                    start, end = end, time.time()
    except Exception as e:
        print(f"server 处理异常： {e}")
    finally:
        selector.close()

if __name__ == '__main__':
    try:
        server('0.0.0.0',6789)
    except KeyboardInterrupt:
        print("exit")


