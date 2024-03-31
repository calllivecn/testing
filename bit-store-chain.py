#!/usr/bin/env python3
# coding=utf-8
# date 2021-11-12 22:24:17
# author calllivecn <calllivecn@outlook.com>


import io
import binascii

# 使用一种更好的方式，存储大数。
"""
在存储时使用一个字节的后7bit来保存;
首位1bit当结束标志。

怎么转换？测试可以。查看首位flag: 1
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
    
    store[0] ^= 0x80 # 把最后一个字节的首位bit置1。
    store.reverse()
    return store

# 从 bytearray + memoryview 里读取。
def store2number(mv, cur=0):
    n = 0
    while ((b := mv[cur]) >> 7) != 1:
        n = (n<<7) + b
        cur += 1

    n = (n<<7) + (mv[cur] ^ 0x80) # 把最后一个字节的首位bit置0。
    return n

def store2number4byte(buf):
    n = 0
    for b in buf[:-1]:
        n = (n<<7) + b

    n = (n<<7) + (buf[-1] ^ 0x80) # 把最后一个字节的首位bit置0。
    return n

# flag: 1 END




def show(n: int):
    print("-"*40)
    print("big bytes:", number2byte(n))
    print("little bytes:", number2byte(n, "little"))
    print(f"hex(): 0x{n:x}")
    print(f"bin(): {n:b}")
    print("-"*40)


import buffer

big_number = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffff
big_number = 0x01020304

buf = buffer.Buffer()

print("有多少个bit: ", big_number.bit_length())
test = number2store(big_number)

buf[:len(test)] = test

print(binascii.b2a_hex(number2byte(big_number)[0]), "转换为7bit链式存储：", binascii.b2a_hex(test))
print("还原：", hex(store2number(test)))
