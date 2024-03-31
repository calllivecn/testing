#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 21:18:37
# modify 2022-08-01 11:16:07
# author calllivecn <calllivecn@outlook.com>


import os
import sys
import binascii
import socket
from hashlib import sha256, pbkdf2_hmac

from cryptography import exceptions
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class NonceMaxError(Exception):
    pass

class Nonce:
    """
    Nonce 的含意是，每个密码对，每次加密中都不能重复使用同一个None值。
    重点是不同。
    """

    def __init__(self):

        self.__max = 0xffffffffffffffffffffffff
        self.__nonce = 0
        print("nonce type:", type(self.__nonce))

    @property
    def nonce(self):
        i = self.__nonce
        self.__nonce += 1
        if self.__nonce > self.__max:
            raise NonceMaxError("None value too max")
        return i.to_bytes(12, "big")
    
    @nonce.setter
    def nonce(self, value):
        self.__nonce = value
    
    def get_nonce(self):
        return self.__nonce


# 要想使用使用密码验证，不能这么用，而是使用临时密钥协商好后，在进行一般的密码验证。
def genkey(password, salt=b""):
    key = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 2000)
    return key


ADDR = "0.0.0.0" 
ADDR = "::" 
PORT = 6789


# 可以不用AAD, wiregurad 就没用。
AAD="整个软件指定一个値？".encode("utf8")
AAD=None

def server():
    password = "这是一个AESGCM密码"
    
    key = genkey(password)
    
    aesgcm = AESGCM(key)

    print("password:", password)

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind((ADDR, PORT))

    nonce = Nonce()

    try:
        while True:
            data, addr = sock.recvfrom(8192)

            try:
                text = aesgcm.decrypt(nonce.nonce, data, AAD)
            except exceptions.InvalidTag:
                print(f"Nonce: {nonce.get_nonce()} 从 {addr} 接收到错误数据： {binascii.b2a_hex(data)}")
                continue

            print("Nonce:", nonce.get_nonce(), "Server 解密：", text)

            """
            if text == b"quit.":
                print("server done, exit.")
                break
            """
    except KeyboardInterrupt:
        sock.close()


def client(password, addr, n=None, server_exit=False):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

    key = genkey(password)

    nonce = Nonce()

    if n:
        nonce.nonce = n

    aesgcm = AESGCM(key)

    for i in range(10):
        print("="*20)
        data = b"varible data: " + str(i).encode("ascii") + b" --- " + os.urandom(16)
        print(f"加密前长度：{len(data)}\n数据：{data}")

        cipher = aesgcm.encrypt(nonce.nonce, data, AAD)
        print(f"Nonce: {nonce.get_nonce()} 长度：{len(cipher)}\n密后：{cipher}")

        sock.sendto(cipher, (addr, PORT))


    if server_exit:
        cipher = aesgcm.encrypt(nonce.nonce, b"quit.", AAD)
        sock.sendto(data, (addr, PORT))
        print("client done")
    
    sock.close()



if __name__ == "__main__":

    if sys.argv[1] == "server" and len(sys.argv) == 2:
        server()
    elif sys.argv[1] == "client" and len(sys.argv) == 5:
        password = sys.argv[2]
        n = int(sys.argv[3])
        server_addr = sys.argv[4]
        client(password, server_addr, n)
    else:
        print(f"{sys.argv[0]} <server|client>")

