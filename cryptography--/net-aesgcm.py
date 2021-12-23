#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 21:18:37
# author calllivecn <c-all@qq.com>


import os
import sys
import binascii
import hashlib
import socket
from hashlib import sha256, pbkdf2_hmac

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


"""
class server:

    def __init__(self, sock, key, nonce, aad):
        self.sock = sock
        self._key = key
        self._nonce = nonce
        self._aad = aad

    
    def encrypt(self, data):

"""

class Nonce:

    def __init__(self):

        self.__max = 0xffffffffffffffffffffffff

        self.__nonce = int.from_bytes(os.urandom(12), "big")
        print("nonce type:", type(self.__nonce))

    @property
    def nonce(self):
        return self.__nonce.to_bytes(12, "big")
    
    @nonce.setter
    def nonce(self, value):
        self.__nonce = value
    
    def add(self):
        self.__nonce += 1


def genkey(password, salt):
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 2000)
    return key



ADDR = ("127.0.0.1", 6789)

# 那这里，需要两边预有的。
# password, salt, aad


def server():
    password = "这是一个AESGCM密码"
    
    salt = os.urandom(16)
    
    aad = os.urandom(16)
    
    key = genkey(password, salt)
    
    aesgcm = AESGCM(key)

    print("password:", password, "salt:", binascii.b2a_hex(salt), "aad:", binascii.b2a_hex(aad))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(ADDR)
    #sock.listen(5)

    #client, addr = sock.accept()
    #print("连接：", addr)


    while True:
        data, addr = sock.recvfrom(8192)
        print("从接收：", addr)

        nonce = data[:12]
        text = aesgcm.decrypt(nonce, data[12:], aad)
        print("Server 解密：", text)
        if text == b"quit.":
            print("server done, exit.")
            break
    
    sock.close()
    #client.close()


def client(password, salt, aad):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.connect(("127.0.0.1", 6789))

    key = genkey(password, salt)

    nonce = Nonce()

    aesgcm = AESGCM(key)

    for i in range(7):

        data = b"varible data: " + str(i).encode("ascii")
        print("Client 加密前：", data)

        nonce.add()
        cipher = aesgcm.encrypt(nonce.nonce, data, aad)

        data = nonce.nonce + cipher
        sock.sendto(data, ADDR)


    nonce.add()
    cipher = aesgcm.encrypt(nonce.nonce, b"quit.", aad)
    data = nonce.nonce + cipher
    sock.sendto(data, ADDR)
    print("client done")
    
    sock.close()


if __name__ == "__main__":
    if sys.argv[1] == "server":
        server()
    elif sys.argv[1] == "client":
        password = sys.argv[2]
        salt = binascii.a2b_hex(sys.argv[3])
        aad = binascii.a2b_hex(sys.argv[4])
        print(password, salt, aad)
        client(password, salt, aad)
    else:
        print(f"{sys.argv[0]} <server|client>")

