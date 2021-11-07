#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-12 22:24:17
# author calllivecn <c-all@qq.com>


import binascii

# 使用一种更好的方式，存储大数。
"""
在存储时使用一个字节的后7bit来保存;
首位1bit当结束标志。

怎么转换？以测试可以。查看flag: 1
"""

def number2byte(n, order="big"):
    """
    n : 大数，一般是超过机器字长的。
    return : bytes n, s字节数
    """
    s, c = divmod(n.bit_length(), 8)
    if c > 0:
        s+=1
    
    return n.to_bytes(s, order), s


# flag: 1 BEGIN
def number2store(n):
    store = bytearray()
    while n>0:
        print("n:", bin(n))
        store.append(n & 0x7f) # 取出后7bit
        n>>=7
    
    store[0] ^= 0x7f # 把最后一个字节的首位置1。
    store.reverse()
    return store

def store2number(buf):
    n = 0
    for b in buf[:-1]:
        n = (n<<7) + b

    n = (n<<7) + (buf[-1] ^ 0x7f)
    return n
    
# flag: 1 END




def show(n: int):
    print("-"*40)
    print("big bytes:", number2byte(n))
    print("little bytes:", number2byte(n, "little"))
    print(f"hex(): 0x{n:x}")
    print(f"bin(): {n:b}")
    print("-"*40)


big_number = 0x01020304

test = number2store(big_number)
print(binascii.b2a_hex(number2byte(big_number)[0]), "转换为7bit链式存储：", binascii.b2a_hex(test))
print("还原：", hex(store2number(test)))
