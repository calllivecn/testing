#!/usr/bin/env python3
#coding=utf-8
# date 2018-04-08 06:00:42
# author calllivecn <calllivecn@outlook.com>

import argparse
from hashlib import sha256
import os
import sys
import time
from os.path import split,join,isfile,isdir,exists,abspath,islink
from struct import pack, unpack
from threading import Thread

try:
    from Crypto.Cipher import AES
except ModuleNotFoundError:
    print("请运行pip install pycrypto 以安装依赖")
    exit(2)

PROGRAM = sys.argv[0]

FORMAT_VERSION = 1

class PromptTooLong(Exception):
    pass

class StoreFormat:
    """
    写入到文件的文件格式
    """
    
    def __init__(self, prompt, out_fp):
        """
        prompt: `str': 密码提示信息
        out_fp: `fp': 类文件对象
        """

        self.version = FORMAT_VERSION  # 1byte
        self.iv = os.urandom(30)     # 30byte
        self.salt = os.urandom(32)   # 32byte
        self.long = bytes(8)         # 8byte 加密后数据部分长度
        self.sha256 = bytes(32)      # 32byte 加密后数据部分校验和
        self.prompt = bytes(4096)   # 定长，utf-8编码串, 之后填写，可为空
        self.header_len = 1 + 1 + 30 + 32 + 8 + 32 + 4096
        
        # 放在数据的后面，也就是文件的最后。
        self.fill = 0                # 1byte

        # 以上就格式顺序

        prompt = prompt.encode("utf-8")
        if len(prompt) > 4096:
            raise PromptTooLong("你给的密码提示信息太长。(utf8编码后>4096字节)")
        else:
            self.prompt = prompt

        FORMAT="!BBH"
        headers = pack(FORMAT, 1, 0, slef.prompt_len)

        self.HEAD = headers + self.iv + self.salt + self.prompt

    def init_(self):
       pass 
    

class AES256:
    """mehtod:
    encrypto() --> block data
    decrypto() --> block data
    
    attribute:
    self.key
    self.key_salt 
    self.iv
    """

    def __init__(self, key, iv):
        """
        key 洒
        """
        self.key = key
        self.iv = iv 
        self.mode = AES.MODE_CBC

        self.fill = 0

        
    def encrypt(self, data):
        """
        data: `byte': 由于AES 256加密块为32字节
            当数据结尾加密块不足32字节时，
            填充空字节。
        return: `byte': 加密字节
        """
        encryptor = AES.new(self.key, self.mode, self.iv)

        data_len = len(data)

        blocks, rema = divmod(data_len, 32)

        if rema == 0:
            return encryptor.encrypt(data), rema

        else:
            self.fill = 32 - rema
            return encryptor.encrypt(data + bytes(self.fill)), rema

    def decrypt(self, data, fill=0):
        """
        data: `byte': 需解密数据
        fill: `int': 0~31 number
        return: `byte':
        """

        decryptor = AES.new(self.key, self.mode, self.iv)

        # 这样是不行的 !
        #dedata = decryptor.decrypt(data)
        #return dedata.rstrip(b'\0')

        # if fill != 0 说明这是最后一块，且有填充字节。
        if fill != 0:
            return decryptor.decrypt(data)
        else:
            data = decryptor.decrypt(data)
            return data[0:-fill]


def test():
    import logging
    from binascii import b2a_hex

    logger = logging.getLogger("root-logger")
    console = logging.StreamHander()
    #console.setLevel(logging.WARNING)
    console.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s %(name)s- %(levelname)s - %(message)s')

    console.setFormatter(formatter)

    logger.addHander(console)

    salt = os.urandom(30)
    iv = os.urandom(16)
    key = sha256(salt + "这是密码".encode()).digest()
    aes = AES256(key, iv)

    origin = "这是中文原文"
    origin_data = origin.encode() + bytes(6)

    print("这是原文本:", origin, "长度:",len(origin.encode()))
    print("这是原文:", b2a_hex(origin_data), "长度:",len(origin_data))
    crypt_data = aes.encrypt(origin_data)
    print("这是密文:", b2a_hex(crypt_data), "长度：", len(crypt_data))
    decode_data = aes.decrypt(*crypt_data)
    print("这是解密后原文:", b2a_hex(decode_data), "长度：", len(decode_data))


def benchmark():
    import random
    from binascii import b2a_hex
    
    salt = os.urandom(30)
    iv = os.urandom(16)
    key = sha256(salt + "这是密码".encode()).digest()
    aes = AES256(key, iv)

    count = 0
    while True:
        count += 1
        origin = os.urandom(random.randint(128, 256))

        encrypt = aes.encrypt(origin)

        decrypt = aes.decrypt(*encrypt)

        if origin != decrypt:
            print("第{}不对了。".format(count))
            print("原文：", b2a_hex(origin))
            print("密码：", b2a_hex(encrypt[0]))
            print("还原文：", b2a_hex(decrypt))
            exit(1)

if __name__ == "__main__":
    #test()
    benchmark()
