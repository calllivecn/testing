#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 22:35:17
# update 2022-08-01 17:35:17
# author calllivecn <c-all@qq.com>

"""
这里测试的是： 对等方的认证加密通信的密钥交换。

~~没有用到 密钥交换。双方是已知对等方 公钥的。~~(不对)

目前的理解是：
1. 是先生成一个临时密钥对，
2. 使用这个临时密钥对，进行密钥交换，之后用来，认证加密传输。
3. 一段时间之后，在轮换新密钥对。

"""

__all__ = (
    "CipherSstate",
    "TransferSession",
    "Transfer",
)


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


# 密钥交换过程
def swapkey(privkey, peer_pubkey, salt=b"", info=b""):
    """
    genkey:bytes --> private_key,
    peer_pubkey:bytes --> peer public key,
    HKDF() 时使用的 salt 和 info: bytes
    return --> 密钥交换，和派生后的对称密钥
    """

    private_key = x25519.X25519PrivateKey.from_private_bytes(privkey)
    shared_key = private_key.exchange(peer_pubkey)
    deriverd_key = HKDF(algorithm=hashes.SHA256, length=32, salt=salt, info=info)
    return deriverd_key.derive(shared_key)


def net_swapkey(sock, peer_pubkey, salt, info):
    pass


class NonceMaxError(Exception):
    pass

class CipherState:

    def __init__(self, key, AAD=None):
        self.key = key
        self.AAD = AAD
        self._n = 0
    
    @property
    def nonce(self):
        self._n += 1
        return self._n.to_bytes(12, "big")
    
    @nonce.setter
    def nonce(self, value):
        if value > 0xffffffffffffffffffffffff:
            raise NonceMaxError("None value too max")
        self._n = value

    def next_nonce(self):
        """
        当前Nonce値, 每次引用后都会自动+1。
        """
        return self._n


class Cipher:
    def __init__(self, CS):
        self._cs = CS

        self.aead = AESGCM(self._cs.key)

        self.encrypter = self.aead.encrypt()
        self.decrypter = self.aead.decrypt()
    
    def encrypt(self, data):
        enc_data = self.encryptr(self._cs.nonce, data, self._cs.aad)
        return enc_data

    def decrypt(self, data):
        data = self.decryptr(self._cs.nonce, data, self._cs.aad)
        return data


class Transfer:

    def __init__(self,)


def server(genkey):

    sock = socket.create_server(("::1", 6789), family=socket.AF_INET6, backlog=128)

    client, addr = sock.accept()
    sock.close()

    # 密码交换
    net_swapkey()

    # generate pubk
    pubkey = x25519.X25519PrivateKey.from_private_bytes(genkey)


    while True:

        data = generate_data()
        enc_data = session.encrypt(nonce, data, aad)

        client.send(enc_data)


def net_chacha20_client(key):
    sock = socket.create_connection(("::1", 6789))

    chacha20 = 




# peer 1
pkey1 = b"mAJGO9nzQ/aPCz8mPqAxGCcJmiEAyZ78rVC+Z1YP2nM="

# pper 2
pkey2 = b"OFl5iDjKS5X4O+A0AMm8Xqdh9+AXmtXp+jmfBhjP2H8="
