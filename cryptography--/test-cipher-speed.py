#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-06 21:18:37
# author calllivecn <c-all@qq.com>


import os
import sys
import time
import binascii
import base64


from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import (
    ec,
    x25519,
    ed25519,
)

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


## chacha20p
print("chacha20poly1305 加解密测试===========")

# 生成key

genkey = ChaCha20Poly1305.generate_key()

text = "这是使用认证加密的数据。"
print("原文：", text)

aad = b"authenticated but unencrypted data"

# 和上面使用同一个私钥可行，但不应该，这里先实验。
chacha20 = ChaCha20Poly1305(genkey)

#####################################
#
# nonce 在每次加密时，不能重复。可以 +1 操作.
#
######################################
nonce = os.urandom(12)

cipher_text = chacha20.encrypt(nonce, text.encode("utf-8"), aad)

print("密文：", base64.b64encode(cipher_text))

decipher_text = chacha20.decrypt(nonce, cipher_text, aad)

print("解文：", decipher_text.decode("utf-8"))


## AESGCM

print("chacha20poly1305 加解密测试===========")
text = "这是 AESGCM 加密明文"

data = text.encode("utf8")
print("原文：", text, "lenght:", len(data))

aad = b"authenticated but unencrypted data"

#key = AESGCM.generate_key(bit_length=128)
key = AESGCM.generate_key(256)
aesgcm = AESGCM(key)

nonce = os.urandom(12)

ct = aesgcm.encrypt(nonce, data, aad)
print("密文:", ct, "lenght:", len(ct))

de_data = aesgcm.decrypt(nonce, ct, aad)

print("解文:", de_data.decode("utf8"))


sys.exit(0)


#########################
#
# 需要签名
#
##########################


genkey1 = x25519.X25519PrivateKey.generate()
pubkey1 = genkey1.public_key()
genkey1_bytes = genkey1.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
pubkey1_bytes = pubkey1.public_bytes(Encoding.Raw, PublicFormat.Raw)


instance_ed25519_genkey = ed25519.Ed25519PrivateKey.from_private_bytes(genkey1_bytes)

print("match x25519 genkey ed25519 genkey", base64.b64encode(genkey1_bytes), base64.b64encode(instance_ed25519_genkey.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())))

data = aad + nonce

signature1 = instance_ed25519_genkey.sign(data)

print("ed25519 signature:", base64.b64encode(signature1))


instance_ed25519_pubkey = ed25519.Ed25519PublicKey.from_public_bytes(pubkey1_bytes)

sign_verify = instance_ed25519_pubkey.verify(signature1, data)

print("验证签名", sign_verify)