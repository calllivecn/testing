#!/usr/bin/env python3
# coding=utf-8
# date 2018-12-24 16:01:53
# https://github.com/calllivecn

from pprint import pprint

import pymysql

con = pymysql.connect(
                        host="localhost",
                        port=13306,
                        user="zhangxu",
                        password="mysql57",
                        db="zhangxu",
                        )

sql = """insert into this_my(name,id,phone) values(%s,%s,%s);"""

cursor = con.cursor()

fetch_sum = cursor.execute(sql,("卟上中茜","1314","123456"))

print(fetch_sum)

#cursor.close()

con.commit()

query = """select * from this_my"""
cursor.execute(query)
result = cursor.fetchall()

pprint(result)

con.close()
