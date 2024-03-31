#!/usr/bin/env python3
# coding=utf-8
# date 2020-07-16 09:27:42
# author calllivecn <calllivecn@outlook.com>

import sys
import ssl
import binascii
import random
from pprint import pprint

import pymysql


def randomdata(count=10000):
    data = []
    for i in range(count):
        r = random.randint(8, 64)
        text = binascii.b2a_hex(ssl.RAND_bytes(r)).decode()
        data.append((r, text))

    return data

con = pymysql.connect(
                        host="localhost",
                        port=3306,
                        user="root",
                        password="zxmysql",
                        db="test",
                        )

sql = """insert into milliontest(id, text) values(%s, %s);"""

cursor = con.cursor()

c = 0
for i in range(int(sys.argv[1])):

    if c == 10:
        c = 0
        print("已经写入10万条了")
    else:
        c += 1

    fetch = cursor.executemany(sql, randomdata())
    con.commit()



query = """select count(id) from milliontest;"""
cursor.execute(query)
result = cursor.fetchall()
print(f"总共有{result}数据")
pprint(result)

con.close()
