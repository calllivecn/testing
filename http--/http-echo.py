import selectors
import socket
import time

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
    data = conn.recv(1024)  # Should be ready
    #print("read():", data)
    # send http response
    conn.send(httpResponse(b"hello world!\n"))
    sel.unregister(conn)
    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()

sock = socket.socket()
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
sock.bind(('0.0.0.0', 6789))
sock.listen(128)
sock.setblocking(False)

sel = selectors.DefaultSelector()
sel.register(sock, selectors.EVENT_READ, accept)

start = time.time()
count = 0

try:
    while True:

        for key, mask in sel.select():
            callback = key.data
            callback(key.fileobj, mask, sel)

            #count += 1
            #end = time.time()

            #if end - start >= 1:
            #    print("count: {}/s".format(count))
            #    start, end = end, time.time()
            #    count = 0
except KeyboardInterrupt as e:
    print("exception: ", e)
finally:
    sock.close()
    sel.close()
