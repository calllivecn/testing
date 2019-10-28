#!/usr/bin/env python3
#coding=utf-8

import time
import socket
import selectors



def echo_handler(conn, event, sel):
    message = conn.recv(4096)
    if message:
        conn.send(message)
    else:
        sel.unregister(conn)
        conn.close()

def handler_accept(conn, event, sel):
    sock , addr = conn.accept()
    sock.setblocking(False)
    sel.register(sock, selectors.EVENT_READ, echo_handler)

def server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    listener.setblocking(False)
    listener.bind((host, port))
    listener.listen(128)

    selector = selectors.DefaultSelector()
    selector.register(listener, selectors.EVENT_READ, handler_accept)

    task_count = 0
    start = 0
    try:
        while True:
            for key, event in selector.select():
                conn = key.fileobj
                func = key.data
                func(conn, event, selector)

                if conn is not listener:
                    task_count += 1
                    end = time.time()
                    if (end - start) >= 1:
                        print("当前处理连接数：{}/s".format(task_count))
                        task_count = 0
                        start = time.time()
    finally:

        selector.close()

if __name__ == '__main__':
    try:
        server('0.0.0.0',6789)
    except KeyboardInterrupt:
        pass


