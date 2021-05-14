#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-13 21:38:26
# author calllivecn <c-all@qq.com>



import sys
import socket
import ipaddress
from selectors import (
                        DefaultSelector,
                        SelectSelector,
                        EVENT_READ,
                        EVENT_WRITE,
                    )


class Selector(SelectSelector):

    EVENT_EXCEPT = (1<<2)

    def __init__(self):
        super().__init__()
        self._excepts = set()

    def select(self, timeout=None):
        timeout = None if timeout is None else max(timeout, 0)
        ready = []
        try:
            r, w, e = self._select(self._readers, self._writers, self._excepts, timeout)
        except InterruptedError:
            return ready, []

        print("e:", e)

        r = set(r)
        w = set(w)
        for fd in r | w:
            events = 0
            if fd in r:
                events |= EVENT_READ
            if fd in w:
                events |= EVENT_WRITE

            key = self._key_from_fd(fd)
            if key:
                ready.append((key, events & key.events))
        
        return ready, list(e)


PORT = 6789
SECRET = "zx"

def httpResponse(msg):
    msg = "<h1>" + msg + "</h1>\n"
    msg = msg.encode("utf8")
    response = [
            "HTTP/1.1 200 ok",
            "Server: server",
            "Content-Type: text/html;charset=UTF-8",
            "Content-Length: " + str(len(msg)),
            "\r\n",
            ]
    data = "\r\n".join(response).encode("utf8") + msg
    return data


def return_ip(conn):
    ip46, port, _, _ = conn.getpeername()

    ip46 = ipaddress.IPv6Address(ip46)
    if ip46.ipv4_mapped:
        ip = ip46.ipv4_mapped
    else:
        ip = ip46.compressed

    conn.send(httpResponse(str(ip)))
    conn.close()


def except_handler(conn, selector):
    print(conn, "能抓到异常")
    conn.close()
    selector.unregister(conn)

def send_handler(conn, selector):
    return_ip(conn)
    selector.unregister(conn)


def recv_handler(conn, selector):

    addr = conn.getpeername()
    print("client:", addr, file=sys.stderr)

    try:
        data = conn.recv(1024)
    except Exception:
        print("conn timeout:", conn.fileno())
        conn.close()
        selector.unregister(conn)
        return

    if data:

        try:
            content = data.decode()

            oneline = content.split("\r\n")[0]

            method, path, protocol = oneline.split(" ")
        except UnicodeDecodeError as e:
            print(e, addr)
            selector.modify(conn, EVENT_WRITE, send_handler)
            return
        except Exception as e:
            print("有异常:", e)
            selector.modify(conn, EVENT_WRITE, send_handler)
            return

        if path == "/" + SECRET:
            return_ip("哈哈，可以样。")
        else:
            return_ip(conn)

    # peer 没有发送数据就close
    conn.close()
    selector.unregister(conn)


def handler_accept(conn, selector):
    sock , addr = conn.accept()
    # sock.settimeout(3) 这种在非阻塞IO下无效
    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, )
    sock.setblocking(False)
    selector.register(sock, EVENT_READ, recv_handler)


def httpmcsleep():

    sock6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    #sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    sock6.bind(("::", PORT))
    
    sock6.listen(128)

    sock6.setblocking(False)

    # selector = DefaultSelector()
    selector = Selector()
    selector.register(sock6, EVENT_READ, handler_accept)

    try:
        while True:
            # event_list = selector.select(1)
            event_list, excepts = selector.select(1)

            for key, event in event_list:
                print(f"selector.select() --> {event}")
                conn = key.fileobj
                func = key.data
                func(conn, selector)
            
            # selector.select(0.1) 超时处理。
            #if PLUGIN_RELOAD == True:
                #print(dir(selector.get_map()))

            if len(event_list) == 0:
                print("selector.select() timeout")
                # import pprint
                # pprint.pprint(selector.get_map().values())

    except Exception as e:
        print(f"httpmcsleep() 异常： {e}", file=sys.stderr)
        raise e

    finally:
        sock6.close()
        selector.unregister(sock6)
        selector.close()


if __name__ == "__main__":
    print(f"listen: :: {PORT}")
    httpmcsleep()