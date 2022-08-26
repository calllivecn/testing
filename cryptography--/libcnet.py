#!/usr/bin/env python3
# coding=utf-8
# date 2022-08-04 06:37:07
# author calllivecn <c-all@qq.com>


__all__ = (
    "Cipher",
    "Transfer",
    "PROTOCOL_NUMBER",
    "NetCipherError",
    "NonceMaxError",
    "HandshakeError",
    # 这几个可能还要思考下
    "privkey2base64",
    "pubkey2base64",
    "base64privkey",
    "base64pubkey",
)


import io
import ssl
import time
import enum
import random
import socket
import base64
import struct
import hashlib

from typing import (
    Union,
)


from cryptography import exceptions
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
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
    # rand_data = ssl.RAND_bytes(random.randint(128, 512))
    rand_data = ssl.RAND_bytes(random.randint(512, 4096))
    sha256 = hashlib.sha256(rand_data)

    return sha256.digest() + rand_data

def verity_data(data):
    sha = data[:32]
    now = hashlib.sha256(data[32:])
    if sha == now.digest():
        return True
    else:
        return False

# key to base64
def privkey2base64(private_key: x25519.X25519PrivateKey) -> base64.b64encode:
    private_bytes = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return base64.b64encode(private_bytes)

def pubkey2base64(public_key: x25519.X25519PublicKey) -> base64.b64encode:
    public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return base64.b64encode(public_bytes)

# base64 to key
def base64privkey(p: str) -> x25519.X25519PrivateKey:
    pe = p.encode("ascii")
    # print(f"Privkey: {pe}")
    b = base64.b64decode(pe)
    return x25519.X25519PrivateKey.from_private_bytes(b)

def base64pubkey(p: str) -> x25519.X25519PublicKey:
    pe = p.encode("ascii")
    # print(f"Pubkey: {pe}")
    b = base64.b64decode(pe)
    return x25519.X25519PublicKey.from_public_bytes(b)


class NetCipherError(Exception):
    pass

class HandshakeError(NetCipherError):
    pass

class NonceMaxError(NetCipherError):
    pass

class Cipher:

    def __init__(self, key: bytes, AAD: Union[None, bytes] = None):
        self.key = key
        self.AAD = AAD
        self._n = 0

        self._timestamp = time.time()

        self.aead = AESGCM(self.key)

    def timestamp_expire(self, interval: int =180) -> bool:
        if (time.time() - self._timestamp) >= interval:
            return True
        else:
            return False
    
    @property
    def nonce(self) -> bytes:
        self._n += 1
        return self._n.to_bytes(12, "big")
    
    @nonce.setter
    def nonce(self, value: int):
        if value > 0xffffffffffffffffffffffff:
            raise NonceMaxError("None value too max")
        self._n = value

    def next_nonce(self) -> int:
        """
        当前Nonce値, 每次引用前都会自动+1。
        """
        return self._n

    def encrypt(self, data: bytes) -> bytes:
        enc_data = self.aead.encrypt(self.nonce, data, self.AAD)
        return enc_data

    def decrypt(self, data: bytes) -> bytes:
        data = self.aead.decrypt(self.nonce, data, self.AAD)
        return data



# 当前使用的协议版本
PROTOCOL_NUMBER = 0x01

HKDF_INFO="今天是个好天气呀！咿呀咿呀咿！".encode("utf8")

class PacketType(enum.IntEnum):
    Reserved = 0 # 保留
    Initiator = enum.auto()
    Responder = enum.auto()
    Rekey = enum.auto()
    Transfer = enum.auto()

class Packet:
    """
    --------------
    0x01 Initiator packet:
    1B version
    1B packet type
    2B payload length
        payload:
            32B Epub, 32B+16B encrypt(Spub)
    --------------
    0x02 Responder packet:
    1B version
    1B packet type
    2B payload length
    payload:
        32B Epub
    --------------
    0x03 rekey packet: 格式与 0x02 相同
    --------------
    0x04 transfer packet:
    前面与0x01 相同, payload 为负载的加密数据
    --------------
    """
    ph = struct.Struct("!BBH")
    protohsize = ph.size

    def __init__(self, Version: int = PROTOCOL_NUMBER, typ: PacketType =PacketType.Initiator):

        self.Version = Version
        self.typ = typ
        self.payload_len = 0

    def from_buf(self, header: bytes):
        self.Version, self.typ, self.payload_len = self.ph.unpack(header)
        self.typ = PacketType(self.typ)

    def to_initiator_buf(self, Epub: bytes, sSpub: bytes) -> memoryview:
        buf = io.BytesIO()
        self.payload_len = 80 # 32 + 32 + 16
        buf.write(self.ph.pack(self.Version, self.typ, self.payload_len))
        buf.write(Epub)
        buf.write(sSpub)
        return buf.getbuffer()

    def to_responder_buf(self, Epub: bytes) -> memoryview:
        buf = io.BytesIO()
        self.payload_len = 32 # Epub 32B
        buf.write(self.ph.pack(self.Version, self.typ, self.payload_len))

        buf.write(Epub)
        return buf.getbuffer()
        
    def to_rekey_buf(self, Epub: bytes) -> memoryview:
        self.payload_len = 32 # Epub 32B
        buf = io.BytesIO()
        buf.write(self.ph.pack(self.Version, self.typ, self.payload_len))

        buf.write(Epub)
        return buf.getbuffer()
    
    def to_transfer_buf(self, payload: bytes) -> memoryview:
        self.payload_len = len(payload)
        buf = io.BytesIO()
        buf.write(self.ph.pack(self.Version, self.typ, self.payload_len))

        buf.write(payload)
        return buf.getbuffer()


class Transfer:

    def __init__(self, sock: socket.SocketType):
        self.sock = sock

    def server(self, Spriv: str, peers: str):
        self.Spriv = base64privkey(Spriv)
        self.Spub = self.Spriv.public_key()
        print(f"peers: {peers}")
        self.peers = tuple(map(lambda p: base64.b64decode(p.encode("ascii")), peers))

        try:
            self.Responder()
        except exceptions.InvalidTag:
            raise HandshakeError("handshake fail.")

    def connect(self, Sprivkey: str, PeerSpubkey: str):
        self.Spriv = base64privkey(Sprivkey)
        self.Spub = self.Spriv.public_key()
        # print(f"peers: {PeerSpubkey}")
        self.PeerSpubkey = base64pubkey(PeerSpubkey)

        try:
            self.Initiator()
        except exceptions.InvalidTag:
            raise HandshakeError("handshake fail.")
    
    def read(self) -> bytes:
        pk = Packet()
        header = self.__read(pk.protohsize)
        if header == b"":
            return b""

        pk.from_buf(header)

        if pk.typ == PacketType.Rekey:
            Epub_bytes = self.__read(pk.payload_len)
            Epub = x25519.X25519PublicKey.from_public_bytes(Epub_bytes)
            shared_key = self.Spriv.exchange(Epub)
            aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)
            self.Raes = Cipher(aeskey)

            pk = Packet()
            header = self.__read(pk.protohsize)
            pk.from_buf(header)

        en_data = b""
        if pk.typ == PacketType.Transfer:
            en_data = self.__read(pk.payload_len)
        else:
            raise NetCipherError("invalid packet")

        data = self.Raes.decrypt(en_data)
        return data
    
    def write(self, data: bytes):
        if self.Taes.timestamp_expire(5):
            pk = Packet(typ=PacketType.Rekey)
            self.Epriv = x25519.X25519PrivateKey.generate()
            shared_key = self.Epriv.exchange(self.PeerSpubkey)
            aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)
            self.Taes = Cipher(aeskey)
            Epub = self.Epriv.public_key()
            Epub_bytes = Epub.public_bytes(Encoding.Raw, PublicFormat.Raw)
            self.__write(pk.to_rekey_buf(Epub_bytes))

        pk = Packet(typ=PacketType.Transfer)
        en_data = self.Taes.encrypt(data)
        self.__write(pk.to_transfer_buf(en_data))


    def Initiator(self):

        Epriv = x25519.X25519PrivateKey.generate()
        Epub = Epriv.public_key()

        shared_key = Epriv.exchange(self.PeerSpubkey)
        aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)

        # 发送加密器
        self.Taes = Cipher(aeskey)

        Spubkey_cipher = self.Taes.encrypt(self.Spub.public_bytes(Encoding.Raw, PublicFormat.Raw))

        pk = Packet(typ=PacketType.Initiator)
        data = pk.to_initiator_buf(
            Epub.public_bytes(Encoding.Raw, PublicFormat.Raw),
            Spubkey_cipher
        )

        self.__write(data)

        data = self.__read(Packet.protohsize)
        pk = Packet()
        pk.from_buf(data)
        if pk.typ != PacketType.Responder:
            raise NetCipherError("invalid packet")

        data = self.__read(pk.payload_len)
        Epub = x25519.X25519PublicKey.from_public_bytes(data[:32])

        shared_key = self.Spriv.exchange(Epub)
        aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)

        #接收加密器
        self.Raes = Cipher(aeskey)


    def Responder(self):
        pk = Packet()
        data = self.__read(pk.protohsize)
        pk.from_buf(data)
        if pk.typ != PacketType.Initiator:
            raise NetCipherError("invalid packet")

        data = self.__read(pk.payload_len)
        Epub = x25519.X25519PublicKey.from_public_bytes(data[:32])
        sSpub = data[32:]

        shared_key = self.Spriv.exchange(Epub)
        aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)
        #接收加密器
        self.Raes = Cipher(aeskey)

        # 解出接收密钥
        Spub_bytes = self.Raes.decrypt(sSpub)

        self.PeerSpubkey = x25519.X25519PublicKey.from_public_bytes(Spub_bytes)

        # check peer Spub 是否是已知的。
        if Spub_bytes not in self.peers:
            addr = self.sock.getpeername()
            Spub_base64 = pubkey2base64(self.PeerSpubkey)
            raise NetCipherError(f"client: {addr} 验证失败, publick key: {Spub_base64}")

        # 生成发送临时密钥
        Epriv = x25519.X25519PrivateKey.generate()
        Epub = Epriv.public_key()
        shared_key = Epriv.exchange(self.PeerSpubkey)
        aeskey = HKDF(hashes.SHA256(), length=32, salt=None, info=HKDF_INFO).derive(shared_key)

        # 生成发送临时密钥
        self.Taes = Cipher(aeskey)

        pk = Packet(typ=PacketType.Responder)
        self.__write(pk.to_responder_buf(Epub.public_bytes(Encoding.Raw, PublicFormat.Raw)))
    
    def fileno(self) -> int:
        return self.sock.fileno()


    def __read(self, size: int) -> bytes:
        buf = io.BytesIO()
        while (data:= self.sock.recv(size)) != b"":
            buf.write(data)
            size -= len(data)
        
        return buf.getvalue()
    
    def __write(self, payload: bytes):
        l = len(payload)
        v = memoryview(payload)
        n = 0
        while n < l:
            n += self.sock.send(v[n:])
    
    def close(self):
        self.sock.close()
