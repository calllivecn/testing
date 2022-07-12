#!/usr/bin/env python3
# coding=utf-8
# date 2022-07-06 17:21:37
# author calllivecn <c-all@qq.com>


import io
import os
import sys
import time
import enum
import socket
import struct
import hashlib
import configparser
from pathlib import Path

example="""\
[Server]
Secret=
# [可选] 监听地址
#Host=""
Port=17787

[EnableId]
# uint32
Id1=1
#Id2=2
#Id3=3
.
.
.

[1]
Secret=
# /path/to/script
Cmd=
# [可选]命令工作目录
#Cwd=

"""


PYZ_PATH = Path(sys.argv[0])
PWD = PYZ_PATH.parent

name, ext = os.path.splitext(PYZ_PATH.name)

CONF = PWD / (name + ".conf")



def get_server_cfg():
    f = CONF

    if f.exists() and f.is_file():
        conf = configparser.ConfigParser()
        conf.read(str(f))
    else:
        with open(f, "w") as fp:
            fp.write(example)
        
        print(f"需要配置 {f} 文件")
        sys.exit(1)
    
    secret = conf.get("Server", "Secret")
    try:
        host = conf.get("Server", "Host")
    except (configparser.NoOptionError, configparser.NoSectionError):
        host = ""
    port = conf.get("Server", "Port")

    return secret, host, port


def get_client_cfg(id_):
    f = CONF
    id_ = str(id_)
    conf = configparser.ConfigParser()
    conf.read(str(f))

    enableIDs = [ i for _, i in conf.items("EnableId") ]

    if id_ not in enableIDs:
        raise ValueError(f"client ID:{id_} not enable")

    secret = conf.get(id_, "Secret")
    cmd = conf.get(id_, "Cmd")
    try:
        cwd = conf.get(id_, "Cwd")
    except (configparser.NoOptionError, configparser.NoSectionError):
        cwd = None

    return secret, cmd, cwd



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
        """
        secret: client secret
        """
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



class PacketType(enum.IntEnum):
    RESERVED = 0
    VERFIY_REQUEST = enum.auto()
    VERFIY_ACK = enum.auto()
    CMD_ARGS = enum.auto()
    CMD_OUTPUT = enum.auto()
    RECODE = enum.auto()


class Transport:
    
    def __init__(self, conn):

        self.conn = conn

    def client(self, id_, c_secret, s_secret):
        """
        client端验证server
        """

        self.r = Request()
        buf = self.r.make(id_, c_secret)

        self.write(PacketType.VERFIY_REQUEST, buf)
        # s = self.__packet_recv(32)
        ptype, payload = self.read()

        return self.r.verifyAck(payload, s_secret)


    def recv_verify_request(self):
        # payload 4(ID) + 32(sha256)
        ptype, payload = self.read()

        if ptype != PacketType.VERFIY_REQUEST and len(payload) != 36:
            raise PacketError("client request verify invalid")

        self.r = Request()

        self.r.frombuf(payload)

        self.id_client = self.r.id_client

    def server(self, c_secret):
        """
        server端验证client
        """
        if self.r.verify(c_secret):
            self.write(PacketType.VERFIY_ACK, self.r.ack(c_secret))
            return True
        else:
            return False
    
    
    def read(self):
        header = self.__packet_recv(4)

        ptype = int.from_bytes(header[:2], "big")
        size = int.from_bytes(header[2:4], "big")

        payload = self.__packet_recv(size)

        return ptype, payload
    

    def write(self, ptype, data):
        d_len = len(data)
        
        return self.__packet_send(ptype.to_bytes(2, "big") + d_len.to_bytes(2, "big") + data)


    def __packet_recv(self, size):
        data = io.BytesIO()

        while size > 0:
            d = self.conn.recv(size)
            if d == b"":
                raise PacketError("receive Packet Error")

            size -= len(d)
            data.write(d)
        
        return data.getvalue()
    

    def __packet_send(self, data):
        d_len = len(data)
        cur = 0
        while cur < d_len:
            c = self.conn.send(data[cur:])
            cur += c
    

    def close(self):
        # if not self.conn.closed:
        self.conn.close()



