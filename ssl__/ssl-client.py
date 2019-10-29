#!/usr/bin/env python3
#coding=utf-8

import socket
import ssl

s = socket.socket()

#sslcontext = ssl.create_default_context()

sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
#sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_3)


verify = 1

if verify:
    sslcontext.verify_mode = ssl.CERT_REQUIRED
    sslcontext.check_hostname = True
    sslcontext.load_verify_locations("ca.crt")

print(sslcontext.check_hostname)

site="localhost"

s = sslcontext.wrap_socket(sock=s, server_hostname=site)
print("连接前。。")
print(s.shared_ciphers())
print(s.cipher())
print(s.version())

s.connect((site, 6789))

print("连接后。。")
print(s.shared_ciphers())
print(s.cipher())
print(s.version())

print('recv --> testing TLS1_2')
s.send('testing TLSv1_2'.encode())
s.recv(1024)
s.close()

