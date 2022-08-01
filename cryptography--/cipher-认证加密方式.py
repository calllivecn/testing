#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 03:48:45
# author calllivecn <c-all@qq.com>

"""
对称加密链接：
https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/?highlight=AES#cryptography.hazmat.primitives.ciphers.algorithms.AES

认证加密链接：
https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.ChaCha20Poly1305
"""

import os

# 对称加密
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    algorithms,
    modes,
)



def chacha20():
    text = "1234567890"
    print("原文:", text)

    key = os.urandom(32)
    nonce = os.urandom(16)

    algorithm = algorithms.ChaCha20(key, nonce)
    cipher = Cipher(algorithm, mode=None)
    
    encryptor = cipher.encryptor()
    ct = encryptor.update(text.encode("utf-8"))
    
    print("加密数据:", ct)
    
    decryptor = cipher.decryptor()
    t = decryptor.update(ct)
    
    print("解密数据:", t.decode("utf-8"))


def aes():
    text = "1234567890"
    print("原文:", text)

    key = os.urandom(32)
    iv = os.urandom(16)

    algorithm = algorithms.AES(key)

    # 查看 CFB 和 CFB8 是不是一样的。 # CFB 和 CFB8 不一样。。。。。！！！xxxxx
    # cipher = Cipher(algorithm, mode=modes.CFB8(iv))
    cipher = Cipher(algorithm, mode=modes.CFB(iv))
    
    encryptor = cipher.encryptor()
    ct = encryptor.update(text.encode("utf-8")) + encryptor.finalize()
    
    print("加密数据:", ct)
    
    decryptor = cipher.decryptor()
    t = decryptor.update(ct) + decryptor.finalize()
    
    print("解密数据:", t.decode("utf-8"))


print("加密算法: chacha20")
chacha20()

print()

print("加密算法: aes-256-cfb")
aes()


