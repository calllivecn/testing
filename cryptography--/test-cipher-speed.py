#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 21:18:37
# author calllivecn <c-all@qq.com>


import os
import sys
import time
import binascii


from cryptography.hazmat.primitives.ciphers.aead import (
    AESGCM,
    ChaCha20Poly1305,
)


# 生成key

key = ChaCha20Poly1305.generate_key()

text = "这是使用认证加密的数据。"
print("原文：", text)

aad = b"authenticated but unencrypted data"


chacha20 = ChaCha20Poly1305(key)

# nonce 在每次加密时，不能重复。可以 +1 操作.
nonce = os.urandom(12)

cipher_text = chacha20.encrypt(nonce, text.encode("utf-8"), aad)

print("密文：", binascii.b2a_hex(cipher_text))


decipher_text = chacha20.decrypt(nonce, cipher_text, aad)

print("解文：", decipher_text.decode("utf-8"))