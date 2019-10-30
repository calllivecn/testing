#!/usr/bin/env python3
#coding=utf-8

import socket
import ssl

s = socket.socket()

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

#s.bind(("localhost",6789))
s.bind(("",6789))

s.listen(128)


#sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS)
sslcontext.options |= (ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
sslcontext.load_cert_chain(keyfile="server.key", certfile="server.crt")

def start():

    while True:
        sock, addr = s.accept()

        try:
            sock = sslcontext.wrap_socket(sock, server_side=True)
        except Exception as e:
            print("握手异常：", e)
            sock.close()
            continue

        print('connecting ... ', *addr)
        data = sock.recv(1024)
        print('recv -->', data.decode())
        sock.send(data)
        sock.close()



try:
    start()
except KeyboardInterrupt:
    pass
except Exception as e:
    raise e
    print('异常退出')
finally:
    s.close()
