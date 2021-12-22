#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 21:18:37
# author calllivecn <c-all@qq.com>


import os
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

        self.nonce = self.__nonce
    
    @property
    def nonce(self):
        return self.__nonce.to_bytes(12, "big")
    
    @nonce.setter
    def nonce(self, value):
        self.__nonce = value
        self.nonce = self.__nonce.to_bytes(12, "big")
    
    def add(self):
        self.__nonce += 1
        self.nonce = self.__nonce.to_bytes(12, "big")


def genkey(password, salt):
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 2000)
    return key


salt = os.urandom(16)

aad = salt

nonce = Nonce()

key = genkey("这是一个AESGCM密码")

aesgcm = AESGCM(key)

def server():

    sock = socket.socket()
    sock.bind(("12.0.0.1", 6789))
    sock.listne(5)

    client, addr = sock.accept()
    print("连接：", addr)

    sock.close()

    while True:
        data = client.recv(8192)
        nonce = data[:12]
        aad = data[12:28]
        text = aesgcm.decrypt(nonce, data[28:], aad)
        print("Server 解密：", text)
        if text == b"quit.":
            print("done")
            break
    
    client.close()


def client():


