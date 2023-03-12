#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-12 20:54:41
# author calllivecn <c-all@qq.com>


import socket

# create a bluetooth socket
server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

# bind the socket to a port
#server_sock.bind(("", 1))

server_sock.bind(("8C:C6:81:15:83:BB", 1))

# listen for incoming connections
server_sock.listen(1)

# accept a connection
client_sock, client_info = server_sock.accept()
print("Accepted connection from", client_info)

# receive and send data
try:
    while True:
        data = client_sock.recv(1024)
        if not data:
            break
        print("Received:", data)
        client_sock.send(b"Echo: " + data)
except OSError:
    pass

# close the sockets
print("Disconnected.")
client_sock.close()
server_sock.close()
