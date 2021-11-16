#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 22:35:17
# author calllivecn <c-all@qq.com>


import os
import ssl
import random
import socket
import base64
import hashlib


from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519, ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM,
    ChaCha20Poly1305,
)


def generate_data():
    # data 为 一个随机数，sha256组成，方便对端验证数据传输是否正确。
    rand_data = ssl.RAND_bytes(random.randint(128, 512))
    sha256 = hashlib.sha256(rand_data)

    return sha256 + rand_data

def verity_data(data):
    sha = data[:32]
    now = hashlib.sha256(data[32:])
    if sha == now.digest:
        return True
    else:
        return False

"""
我这里测试的是： 对等方的认证加密通信。

没有用到 密钥交换。双方是已知对等方 公钥的。(不对)

目前的理解是：
1. 是先生成一个临时密钥对，
2. 使用这个临时密钥对，进行密钥交换，之后用来，认证加密传输。
3. 一段时间之后，在轮换新密钥对。

"""

# 密钥交换过程
def key_swap(genkey, peer_pukey, salt, info):
    """
    genkey:bytes --> private_key,
    peer_pubkey:bytes --> peer public key,
    HKDF() 时使用的 salt 和 info: bytes
    return --> 密钥交换，和派生后的对称密钥
    """

    private_key = x25519.X25519PrivateKey.from_private_bytes(genkey)
    shared_key = private_key.exchange(peer_pukey)
    deriverd_key = HKDF(algorithm=hashes.SHA256, length=32, salt=salt, info=info)
    return deriverd_key.derive(shared_key)


    

# 试用 chacha20-poly1305 和使用
class TransferSession:
    def __init__(self, key, aad, nonce=0):
        self.__aad = aad
        self.nonce = nonce

        self.ccp = ChaCha20Poly1305(key)

        self.encrypter = self.ccp.encrypt()
        self.decrypter = self.ccp.decrypt()
    
    @property
    def aad(self):
        return self.__aad
    
    @aad.setter
    def aad(self):
         self.__aad = self.__aad
    
    def encrypt(self, data):
        enc_data = self.encryptr(self.nonce, data, self.aad)
        return enc_data
        # return self.pack()

    def decrypt(self, data):
        data = self.decryptr(self.nonce, data, self.aad)
        return data
        # return self.pack()
    
    def __nonce_change(self):
        self.nonce += 1
        return self.nonce.tobytes(12, "big")




def net_chacha20_server(genkey):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind(("::1", 6789))
    sock.listen(5)

    client, addr = sock.accept()

    sock.close()

    # generate pubk
    pubkey = x25519.X25519PrivateKey.from_private_bytes(genkey)

    

    # 认证加密传输
    chacha20 = ChaCha20Poly1305(key)

    # 这个是身份认证消息
    aad = os.urandom(37)

    nonce = b"0"

    while True:

        data = generate_data()
        enc_data = chacha20.encrypt(nonce, data, aad)

        client.send(enc_data)


def net_chacha20_client(key):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

    sock.connect(("::1", 6789))

    chacha20 = 




# peer 1
pkey1 = b"mAJGO9nzQ/aPCz8mPqAxGCcJmiEAyZ78rVC+Z1YP2nM="

# pper 2
pkey2 = b"OFl5iDjKS5X4O+A0AMm8Xqdh9+AXmtXp+jmfBhjP2H8="
