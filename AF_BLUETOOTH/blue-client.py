#!/usr/bin/env python3
# coding=utf-8
# date 2023-03-12 21:02:56
# author calllivecn <calllivecn@outlook.com>


import socket

# create a bluetooth socket
client_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

# connect to the server
server_addr = "00:11:22:33:44:55" # replace with your server's MAC address
server_addr = "8C:C6:81:15:83:BB" # replace with your server's MAC address
server_port = 1
client_sock.connect((server_addr, server_port))
print("Connected to", server_addr)

# send and receive data
try:
    while True:
        data = input("Enter message: ")
        if not data:
            break
        client_sock.send(data.encode())
        data = client_sock.recv(1024)
        print("Received:", data.decode())
except OSError:
    pass

# close the socket
print("Disconnected.")
client_sock.close()
