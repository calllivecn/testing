#!/usr/bin/env python3
# coding=utf-8
# date 2022-08-02 02:27:21
# author calllivecn <c-all@qq.com>



from cryptography import exceptions
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

private_key1 = X25519PrivateKey.generate()
private_key2 = X25519PrivateKey.generate()

public_key1 = private_key1.public_key()
public_key2= private_key2.public_key()

shared_key1 = private_key1.exchange(public_key2)

derived_key1 = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'handshake data',
).derive(shared_key1)


shared_key2 = private_key2.exchange(public_key1)

# derived_key 和 derived_key_2 应该 是推导出来的相同的对称加密密钥。
derived_key2 = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=None,
    info=b'handshake data',
).derive(shared_key2)

print(f"shared_key1: {shared_key1}")
print(f"shared_key2: {shared_key2}")

print(f"derived_key1: {derived_key1}")
print(f"derived_key2: {derived_key2}")

print("这里在测试下，双方有固定私钥，使用临时私钥对，生成临时对称密码(网络中是收对称密码，和发对称密码)。")

Spriv1 = X25519PrivateKey.generate()
Epriv1 = X25519PrivateKey.generate()

Spriv2 = X25519PrivateKey.generate()
Epriv2 = X25519PrivateKey.generate()


shared_key1 = Epriv1.exchange(Spriv1.public_key())
derived_key1 = HKDF(hashes.SHA256(), length=32, salt=None, info=b"handshake data").derive()



