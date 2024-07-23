#!/usr/bin/env python3
# coding=utf-8
# date 2024-07-22 13:19:44
# author calllivecn <calllivecn@outlook.com>

import sys
from pprint import pprint

import pymysql

from user import Users


dbinfo = Users["mysql"][0]
dbinfo = Users["mysql"][2]


con = pymysql.connect(
                        host=dbinfo["host"],
                        port=dbinfo["port"],
                        user=dbinfo["user"],
                        password=dbinfo["password"],
                        database=dbinfo.get("db"),
                        # charset=dbinfo.charset,
                        )


sql = """show slave status;"""

cursor = con.cursor()
fetch = cursor.execute(sql)

fields = [i[0] for i in cursor.description]
print(fields)
#print(f"{type(cursor)=}, {dir(cursor)=}")

# 把字段头和值合并起来
result = {}
for k, v in zip(fields, cursor.fetchone()):
    result.update({k: v})

pprint(result)


con.close()
