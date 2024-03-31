#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-05 22:57:18
# author calllivecn <calllivecn@outlook.com>



import sys
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    PublicFormat,
    NoEncryption,
)

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)



# private_key = ec.generate_private_key(ec.SECP256K1())
# print(base64.encodebytes(private_key.private_bytes(Encoding.Raw, PublicFormat.Raw)))


private_key = X25519PrivateKey.generate()
private_bytes = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())

public_key = private_key.public_key()
public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)

pre_shared_key = X25519PrivateKey.generate()
pre_shared_bytes = pre_shared_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())

print("private key bytes:", private_bytes)
print("private key base64:", base64.b64encode(private_bytes).decode("utf-8"))

print("public key bytes:", public_bytes)
pkb64 = base64.b64encode(public_bytes).decode("utf-8")
print("public key base64:", pkb64)

print("pre shared key base64:", base64.b64encode(pre_shared_bytes).decode("utf-8"))

# base64 to key
from_bytes_pubkey = X25519PublicKey.from_public_bytes(base64.b64decode(pkb64.encode("utf8")))
print("从bytes 读取pubkey", from_bytes_pubkey)

