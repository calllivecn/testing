
import time
import socket
import select
import selectors


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
    #conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask, sel):
    data = conn.recv(128)  # Should be ready
    if data:
        conn.send(b"Got: " + data)
    else:
        sel.unregister(conn)
        conn.close()


def epoll_accept(sock, epoll, fd2sock):

    max_count = 128
    while (max_count > 0):
        max_count -= 1
        try:
            client, addr = sock.accept()
        except BlockingIOError:
            # 已经accept完。
            break

        # print("accept:", addr)
        client.setblocking(False)

        epoll.register(client.fileno(), select.EPOLLIN | select.EPOLLET)
        fd2sock[client.fileno()] = client


def main():
    listen = ('0.0.0.0', 6789)
    print('listen:', listen)
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
    sock.bind(listen)
    sock.listen(128)
    sock.setblocking(False)

    #sel = selectors.DefaultSelector()
    #sel.register(sock, selectors.EVENT_READ, accept)

    epoll = select.epoll()
    es = select.EPOLLIN | select.EPOLLET

    fd2sock = {sock.fileno(): sock}
    epoll.register(sock, es)

    start = time.time()
    count = 0
    while True:

        events = epoll.poll()
        for fd, event in events:
            # print("event:", event) # 都是 class int:

            key = fd2sock[fd]

            # if event & select.EPOLLERR or event & select.EPOLLHUP:
                # key.close()
                # fd2sock.pop(fd)
                # print("close()")

            if key == sock:
                epoll_accept(sock, epoll, fd2sock)
                # client, addr = sock.accept()
                # epoll.register(client, select.EPOLLIN | select.EPOLLET)
                # fd2sock[client.fileno()] = client

            elif event == select.EPOLLIN:

                # 模拟处理时间
                # time.sleep(1)

                # print("read():", time.monotonic_ns())
                data = key.recv(1024)
                if data:
                    # print("读数据：", data)
                    epoll.modify(fd, select.EPOLLOUT | select.EPOLLET)
                    """
                    # 这样不速度会慢一半!(why?)（使用 apache ab 工具测试的）
                    key.send(b"ok")
                    epoll.unregister(fd)
                    key.close()
                    fd2sock.pop(fd)
                    """

                else:
                    # print("peer close()")
                    epoll.unregister(fd)
                    key.close()
                    fd2sock.pop(fd)
                
            elif event == select.EPOLLOUT:
                # print("EPOLLOUT:", event)
                key.send(httpResponse(data))
                epoll.unregister(fd)
                key.close()
                fd2sock.pop(fd)
                # print("done close()")
            
            else:
                print("????", fd, event)

            """
            count += 1
            end = time.time()

            if end - start >= 1:
               print("count: {}/s".format(count))
               start, end = end, time.time()
               count = 0
            """


    sock.close()
    epoll.close()


if __name__ == "__main__":
    main()
