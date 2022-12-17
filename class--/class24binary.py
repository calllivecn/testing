#!/usr/bin/env python3
# coding=utf-8
# date 2022-12-14 21:09:09
# author calllivecn <c-all@qq.com>

"""
数据类和二进制数据相互转换
Class and binary data conversion to and from
"""

import io
import os
import struct

from dataclasses import dataclass

from collections import (
    OrderedDict,
    namedtuple,
)

from typing import (
    Union,
    Type,
    TypeVar,
)

from typing_extensions import (
    Self,
)


class AESFile:
    """
    这种可以，但还是有点麻烦。
    """
    header = struct.Struct("HHH")

    def __init__(self, f1, f2, f3, payload=b""):
        self.field1 = f1
        self.field2 = f2
        self.field3 = f3

        self.fields = {}

        self.payload = payload

    @classmethod
    def frombuf(cls, data: bytes):
        a = cls(*cls.header.unpack(data[:cls.header.size]))
        return a

    def tobuf(self):
        return self.header.pack(self.field1, self.field2, self.field3) + self.payload
    
    def __str__(self):

        return f"fields: {self.field1} {self.field2} {self.field3}"


# 不行
class BinField:

    def __init__(self, typ: Type, size: int):
        self.typ = typ
        self.size = size

    def __call__(self, offset: int, data: Union[bytes, memoryview]) -> any:
        """
        目前先只支持int
        """
        return self.typ.from_bytes(data)



# 不行
class C2B:
    """
    class和二进制相互转换

    class Packet(my_define):
        verion: Type(int(2))
        cid: Type(int(8))
        Varlen: IntVar()
    
    pack = packet.a = 2

    """

    header = struct.Struct("HHH")
        
    def __init__(self):

        self.fields = self.__annotations__

        print("attr:", self.fields)

        self.point = 0

    # def __getattr__(self, name):
        # return self._d.get(name)
    
    def __setattr__(self, key, value):
        self.__dict__[key] = value
    
    def __str__(self):
        return str(self.__dict__)
    
    @classmethod
    def frombuf(cls, data: Union[bytes, memoryview]) -> Self:
        self = cls()
        for key, value in self.fields.items():
            self.__dict__[key] = value
        
        return self


    def tobuf(self) -> bytes:
        buf = io.BytesIO()
        for key, binfield in self.fields:
            if isinstance(binfield, BinField):
                data = binfield(self[key])
            else:
                data = binfield()

            buf.write(data)
        return buf.getvalue()


print("测试 AESFile()")

data = os.urandom(10)

f = AESFile.frombuf(data)
f2 = f.tobuf()
print(f)
print(f2)


# 测试 第二次尝试
class Frame(C2B):

    def __init__(self):
        super().__init__()

    stream_id: BinField(int, 8)
    payload_len: BinField(int, 8)
    payload: bytes


print("="*40)

f1 = Frame()
# print(dir(f1))
print("测试 Frame.attr = value")
f1.stream_id = 123
f1.payload_len = 8
f1.payload = b"12345678"
print(f1)

print("测试 Frame.frombuf(data)")
f2 = Frame.frombuf(data)

print(f1)