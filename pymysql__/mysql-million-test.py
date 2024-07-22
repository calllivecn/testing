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

from user import Users


dbinfo = Users["mysql"][0]



def randomdata(count=10000):
    data = []
    for i in range(count):
        r = random.randint(8, 64)
        text = binascii.b2a_hex(ssl.RAND_bytes(r)).decode()
        data.append((r, text))

    return data


def rand_person(count=10000):
    data = [ binascii.b2a_hex(ssl.RAND_bytes(random.randint(8, 16))).decode() for _ in range(count) ]
    return data


con = pymysql.connect(
                        host=dbinfo["host"],
                        port=dbinfo["port"],
                        user=dbinfo["user"],
                        password=dbinfo["password"],
                        database=dbinfo["db"],
                        # charset=dbinfo.charset,
                        )


sql = """insert into milliontest(id, text) values(%s, %s);"""

sql = """insert into person(name, age) values(%s, %s);"""

cursor = con.cursor()

c = 0
for i in range(int(sys.argv[1])):

    if c == 10:
        c = 0
        print("已经写入10万条了")
    else:
        c += 1

    #fetch = cursor.executemany(sql, randomdata())
    fetch = cursor.executemany(sql, rand_person())
    con.commit()



query = """select count(id) from milliontest;"""
cursor.execute(query)
result = cursor.fetchall()
print(f"总共有{result}数据")
pprint(result)

con.close()
