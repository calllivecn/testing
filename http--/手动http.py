#!/usr/bin/env python3
# coding=utf-8
# date 2021-02-22 15:30:42
# author calllivecn <c-all@qq.com>


import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ

PORT=6789
TOKEN="/llsijeflkdsjflafsefi"

def httpResponse(msg):
    msg += "\n"
    msg = msg.encode("utf8")
    response = [
            "HTTP/1.1 200 ok",
            "Server: server",
            "Content-Type: text/plain;charset=UTF-8",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    data = "\r\n".join(response).encode("utf8") + msg
    return data


def return_ip(conn):
    ip = conn.getpeername()[0]
    conn.send(httpResponse(ip))
    conn.close()
    

def send_handler(conn, selector):
    ip = conn.getpeername()[0]
    conn.send(httpResponse(ip))
    conn.close()
    selector.unregister(conn)

def recv_handler(conn, selector):

    data = conn.recv(1024).decode()
    oneline = data.split("\r\n")[0]
    print("client:", conn.getpeername())

    try:
        method, path, protocol = oneline.split(" ")
    except Exception as e:
        return_ip(conn)
        selector.unregister(conn)
        return

    if path == TOKEN:
        # check_mc_server_is_running
        conn.send(httpResponse("这里check server is running"))
        conn.close()
        selector.unregister(conn)
    else:
        return_ip(conn)
        selector.unregister(conn)
        
    # selector.modify(conn, EVENT_WRITE, send_handler)

def handler_accept(conn, selector):
    sock , addr = conn.accept()
    sock.setblocking(False)
    selector.register(sock, EVENT_READ, recv_handler)


def httpmcsleep():

    sock4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    sock4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    sock4.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    sock4.bind(("0.0.0.0", PORT))
    sock6.bind(("::", PORT))
    
    sock4.listen(128)
    sock6.listen(128)

    sock4.setblocking(False)
    sock6.setblocking(False)

    selector = DefaultSelector()
    selector.register(sock4, EVENT_READ, handler_accept)
    selector.register(sock6, EVENT_READ, handler_accept)

    try:
        while True:
            for key, event in selector.select():
                conn = key.fileobj
                func = key.data
                func(conn, selector)
    except Exception as e:
        print(f"httpmcsleep() 异常： {e}")
        raise e
    finally:
        selector.close()
        sock4.close()
        sock6.close()


if __name__ == "__main__":
    try:
        httpmcsleep()
    except KeyboardInterrupt:
        print("exit")

