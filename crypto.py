#!/usr/bin/env python3
#coding=utf-8

import sys  
from Crypto.Cipher import AES  
from Crypto import Random
from binascii import b2a_hex, a2b_hex  
from hashlib import sha256
   
class prpcrypt():  
    def __init__(self, key):  
        self.key = sha256(key).digest()
        #self.iv = Random.new().read(16)
        #self.mode = AES.MODE_CBC  
        self.mode = AES.MODE_ECB
       
    #加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数  
    def encrypt(self, text):  
        #cryptor = AES.new(self.key, self.mode, self.iv)  
        cryptor = AES.new(self.key, self.mode)  
        text = text.encode("utf-8")  
        #这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用  
        length = 16  
        count = len(text)  
        add = length - (count % length)  
        text = text + (b'\0' * add)  
        self.ciphertext = cryptor.encrypt(text)  
        #因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题  
        #所以这里统一把加密后的字符串转化为16进制字符串  
        return b2a_hex(self.ciphertext).decode("utf-8")  
       
    #解密后，去掉补足的空格用strip() 去掉  
    def decrypt(self, text):  
        #cryptor = AES.new(self.key, self.mode, self.iv)  
        cryptor = AES.new(self.key, self.mode)
        plain_text = cryptor.decrypt(a2b_hex(text))  
        return plain_text.rstrip(b'\0').decode("utf-8")  
   
if __name__ == '__main__':  
    encpc = prpcrypt(b'keyskeyskeyskeys')      #初始化密钥  
    decpc = prpcrypt(b'keyskeyskeyskeys')      #初始化密钥  


    e = encpc.encrypt("my book is free")  
    d = encpc.decrypt(e)                       
    print(e, d)  
    e = encpc.encrypt("我是一个粉刷匠1231繁體testひらがな")  
    d = encpc.decrypt(e)
    print(e, d)

    e_ecb = prpcrypt(b'1')
    d_ecb = prpcrypt(b'1')
    e = e_ecb.encrypt("0123456789abcdef")
    d = d_ecb.decrypt(e)
    print(e,d)
