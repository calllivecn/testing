#!/usr/bin/env python3
# coding=utf-8
# date 2022-09-09 15:08:07
# author calllivecn <c-all@qq.com>


import enum
import struct
import asyncio
import threading


class Frame:
    """
    frame type:
    
    """

    def __init__(self):
        self.typ = 
        self.


class ConnectPacket:

    VERSION = 0x01

    def __init__(self, CID, typ):

        self.version = self.VERSION # uint32
        self.CID = CID # uint64
        self.typ = typ
        self.number = 0 # packet number
        self.paylaod = b""

        self.PEER = {} # {"addr:port": 

    def frombuf(self, buf):
        self.CID = 
        self.typ = 
    

    def tobuf(self):


