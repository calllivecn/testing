#!/usr/bin/env python3
# coding=utf-8
# date 2018-12-24 17:04:46
# https://github.com/calllivecn



from pprint import pprint

import pymysql

con = pymysql.connect(
                        host="localhost",
                        port=13306,
                        user="zhangxu",
                        password="mysql5.7",
                        db="zhangxu",
                        )

sql = """insert into this_my(name,id,phone) values(%s,%s,%s);"""

cursor = con.cursor()

fetch_sum = cursor.execute("show tables;")

print(fetch_sum)

#cursor.close()

#con.commit()
result = cursor.fetchall()

pprint(result)

con.close()


