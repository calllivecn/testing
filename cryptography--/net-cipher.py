#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 22:35:17
# author calllivecn <c-all@qq.com>



import socket


from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM,
    ChaCha20Poly1305,
)




# 试用 chacha20-poly1305 和使用
# class safenetwork:
    # def __init

def net_chacha20():
    sock = socket.socket()
    sock.bind(("::1", 6789))
    sock.listen(5)

    client, addr = sock.accept()
    sock.close()

    # 密码交换
    ChaCha20Poly1305()

