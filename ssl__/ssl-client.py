#!/usr/bin/env python3
#coding=utf-8

import socket
import ssl

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 加载系统默认证书，并验证。
#sslcontext = ssl.create_default_context()

# ssl.SSLContext() 默认不进行证书有效性验证。ssl.PROTOCOL_TLS 自动协商最高协议版本。
# 可以使用， context.verify_mode = ssl.CERT_REQUIRED 和 context.check_hostname = True 开启。
sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


# 指定协议版本。 
#sslcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_3)


verify = 1

if verify:
    sslcontext.verify_mode = ssl.CERT_REQUIRED
    sslcontext.check_hostname = True

    # 加载指定证书
    sslcontext.load_verify_locations("ca.crt")


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

