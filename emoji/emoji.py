#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-22 11:08:30
# author calllivecn <calllivecn@outlook.com>


fe = open("emoji.txt","w")

for emoji in range(ord("☀"),ord("🗾")):
    try:
        print("{} ".format(chr(emoji)), end="",file=fe)
    except UnicodeEncodeError:
        print(emoji, "解析不出...")

    
