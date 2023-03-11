
import time
import socket
import select
import selectors


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



def main():
    listen = ('0.0.0.0', 6789)
    print('listen:', listen)
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(listen)
    sock.listen(128)
    #sock.setblocking(False) # 在在异步里没影响

    #sel = selectors.DefaultSelector()
    #sel.register(sock, selectors.EVENT_READ, accept)

    epoll = select.epoll()
    evets = select.EPOLLIN | select.EPOLLPRI | select.EPOLLHUP | select.EPOLLET

    fd2sock = {sock.fileno(): sock}
    epoll.register(sock.fileno(), evets)

    start = time.time()
    count = 0
    while True:

        """
        for key, mask in sel.select():
            callback = key.data
            callback(key.fileobj, mask, sel)
        """

        for fd, event in epoll.poll():
            #print(type(fd), type(event)) # 都是 class int:

            key = fd2sock[fd]

            if event & select.EPOLLERR or event & select.EPOLLHUP:
                key.close()
                fd2sock.pop(fd)
                print("close()")

            elif key == sock:
                client, addr = sock.accept()
                print("accept:", addr)
                #client.setblocking(False)

                epoll.register(client.fileno(), select.EPOLLIN | select.EPOLLET)
                fd2sock[client.fileno()] = client

            elif event == select.EPOLLIN:
                time.sleep(1)
                data = key.recv(1024)
                if data:
                    print("读数据：", data)
                else:
                    print("peer close()")
                    epoll.unregister(fd)
                    key.close()
                    fd2sock.pop(fd)
            
            else:
                print("????", fd, event)

            #count += 1
            #end = time.time()

            #if end - start >= 1:
            #    print("count: {}/s".format(count))
            #    start, end = end, time.time()
            #    count = 0


    sock.close()


if __name__ == "__main__":
    main()
