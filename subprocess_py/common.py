#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-06 17:21:37
# author calllivecn <c-all@qq.com>

import sys
import time
import enum
import socket
import struct
import hashlib

from pathlib import Path


class PacketError(Exception):
    pass

class Request:
    """
    这种不防中间人
    client:
    make(id_, secret_client) --> sendto() --> recv() -- verifyack(buf, secret_secret)
    server:
    recv() --> get_id_conf --> frombuf(buf) --> verify(secret_client) --> ack(secret_server) --> sendto()
    """

    def make(self, id_, secret):
        """
        id: client ID
        secret: client secret
        """
        cur = int(time.time())

        id_byte = struct.pack("!I", id_)

        sha = hashlib.sha256(
            id_byte + secret.encode("ascii") + struct.pack("!Q", cur)
        )

        self.__buf = id_byte + sha.digest()
        return self.__buf

    def frombuf(self, buf):

        if len(buf) != (4+32):
            raise PacketError("packet invalid")

        self.__buf = buf

        self.id_byte = buf[:4]
        self.id_client = struct.unpack("!I", self.id_byte)[0]
        self.sha_client = buf[4:]

    def verify(self, secret):
        cur = int(time.time())
        shas = []
        for t in range(cur - 10, cur + 10):
            sha256 = hashlib.sha256(
                self.id_byte + secret.encode("ascii") + struct.pack("!Q", t)
            )
            shas.append(sha256.digest())

        if self.sha_client in shas:
            return True
        else:
            return False

    def ack(self, secret):
        """
        secret: server secret
        """
        sha256 = hashlib.sha256(
            self.__buf + secret.encode("ascii")
        )
        return sha256.digest()

    def verifyAck(self, buf, secret):
        """
        secret: server secret
        """
        sha256 = hashlib.sha256(
            self.__buf + secret.encode("ascii")
        )

        if buf == sha256.digest():
            return True
        else:
            return False




class Verify:

    def __init__(self, conn, client_secret, server_secret):

        self.conn = conn
        self.c = client_secret
        self.s = server_secret

    def client(self, id_):
        """
        client端验证server
        """

        r = Request()
        buf = r.make(id_, self.c)
        self.conn.send(buf)
        s = self.conn.recv(512)

        # 4 + 16(salt) + 32
        if len(s) != 52:
            raise PacketError("verify Error.")

        return r.verifyAck(s, buf, self.s)


    def server(self, id_):
        """
        server端验证client
        """

        buf = self.conn.recv(512)

         # 4 + 16(salt) + 32
        if len(buf) != 52:
            raise PacketError("verify Error.")

        r = Request()

        r.frombuf(buf)

        if r.verify(self.c):
            self.conn.send(r.ack(self.s))
            return True
        else:
            return False


class PacketType(enum.IntEnum):
    RESERVED = 0
    VERFIY_REQUEST = enum.auto()
    VERFIY_ACK = enum.auto()
    CMD_ARGS = enum.auto()

    RECODE = enum.auto()

class Transport:
    
    def __init__(self, conn):
        self.conn = conn