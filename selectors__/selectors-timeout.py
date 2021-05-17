#!/usr/bin/env python3
# coding=utf-8
# date 2021-05-13 21:38:26
# author calllivecn <c-all@qq.com>


# 想要添加上非阻塞IO的超时机制
# 思路：
# 1. 添加sock.settimeout(35)
#   这样不行，非阻塞IO，settimeout() 无效。
#
# 2. 超时处理部分; 也不行，sleep()，影响并发到没法用。
#    timeout = True
#    for _ in range(RECV_TIMEOUT):
#        try:
#            data = sock.recv(1024)
#        except BlockingIOError:
#            time.sleep(1)
#            continue
#        
#        timeout = False
#        break
#
# 3. 维护一个 双向链表，添加data:(sock, 更新时间戳); 可以用 sock map 快速找到 SockMon()节点在链表中的位置。
#    selector.select(1) 后，check 时间戳是否超时，如果超时，sock.close(), selector.unregister(sock)。
#    1) SockMon(sock: socket, monotoinc: time.monotoinc())
#    2) 双向链表
#    3) 一个 key 为 sock.fd; 值为 SockMon() 节点的 map
#    这样形成一个能从前端删除;后端追加;并可将一个指定节点移动到未尾,并更新时间戳的数据结构。 
#
# 4. Nginx在需要用到超时的时候，都会用到定时器机制。比如，建立连接以后的那些读写超时。
#    Nginx使用红黑树来构造定期器，红黑树是一种有序的二叉平衡树，其查找插入和删除的复杂度都为O(logn)，所以是一种比较理想的二叉树。
#    定时器的机制就是，二叉树的值是其超时时间，每次查找二叉树的最小值，如果最小值已经过期，就删除该节点，然后继续查找，直到所有超时节点都被删除。 


import sys
import time
import socket
import ipaddress
from selectors import (
                        DefaultSelector,
                        EVENT_READ,
                        EVENT_WRITE,
                    )


SECRET = "zx"

PORT = 6789
RECV_TIMEOUT = 19


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

    return httpResponse(str(ip))


def send_handler(conn, msg, selector):
    conn.send(msg)
    conn.close()
    selector.unregister(conn)


def recv_handler(conn, selector):

    data = conn.recv(1024)

    if data:

        path = None

        try:
            content = data.decode()

            oneline = content.split("\r\n")[0]

            method, path, protocol = oneline.split(" ")
        except UnicodeDecodeError as e:
            print(e)
        except Exception as e:
            print("有Exception子类异常:", e)


        if not path and path == "/" + SECRET:
            # 如果没有异常且 secret 是对的
            msg = "这样可以的~！".encode("utf-8")
        else:
            msg = return_ip(conn)

        selector.modify(conn, EVENT_WRITE, lambda conn, selector: send_handler(conn, msg, selector))

    else:
        # peer 没有发送数据就close
        conn.close()
        selector.unregister(conn)


def handler_accept(conn, selector):

    sock, addr = conn.accept()
    # sock.settimeout(3) 这种在非阻塞IO下无效
    sock.setblocking(False)

    addr = sock.getpeername()
    print("client:", addr, file=sys.stderr)

    selector.register(sock, EVENT_READ, recv_handler)


def httpmcsleep():

    sock6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    #sock6.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

    sock6.bind(("::", PORT))
    
    sock6.listen(128)

    sock6.setblocking(False)

    selector = DefaultSelector()
    selector.register(sock6, EVENT_READ, handler_accept)

    try:
        while True:
            event_list = selector.select(1)

            for key, event in event_list:
                print(f"selector.select() --> {event}")
                conn = key.fileobj
                func = key.data
                func(conn, selector)
            
            # selector.select(1) 超时处理。

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
