#!/usr/bin/env python3
#coding=utf-8

import socket,ssl

s = socket.socket()

version = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

s=ssl.SSLSocket(sock=s,keyfile='server_key.pem',certfile='server_cert.pem',
                server_side=True,ssl_version=ssl.PROTOCOL_TLSv1_2)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,True)
s.bind(('',6789))

s.listen(128)


def start():
    while True:
        sock,addr = s.accept()
        print('connecting ... ',*addr)
        data = sock.recv(1024)
        print('recv -->',data.decode())
        sock.send(data)



try:
    start()
except Exception as e:
    raise e
    print('异常退出')
except KeyboardInterrupt:
    pass
finally:
    s.close()
