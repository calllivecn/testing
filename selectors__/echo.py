import selectors
import socket
import time

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    #print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn, mask):
    data = conn.recv(128)  # Should be ready
    if data:
        #print('echoing', repr(data), 'to', conn)
        conn.send(data)  # Hope it won't block
    else:
        #print('closing', conn)
        sel.unregister(conn)
        conn.close()

sock = socket.socket()
sock.bind(('0.0.0.0', 6789))
sock.listen(128)
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)

start = time.time()
count = 0
while True:
    
    for key, mask in sel.select():
        callback = key.data
        callback(key.fileobj, mask)

        count += 1
        end = time.time()

        if end - start >= 1:
            print("count: {}/s".format(count))
            start, end = end, time.time()
            count = 0
