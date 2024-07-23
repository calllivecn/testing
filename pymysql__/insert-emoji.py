#!/usr/bin/env python3
# coding=utf-8
# date 2018-12-24 10:21:55
# https://github.com/calllivecn

import pprint

import pymysql


from user import Users


dbinfo = Users["mysql"][0]

con = pymysql.connect(host=dbinfo["dbinfo"],
                        port=dbinfo["port"],
                        user=dbinfo["user"],
                        password=dbinfo["password"],
                        database=dbinfo.get("db"),
                        charset=dbinfo.get("charset"),
                        )

sql = """insert into emoji(record) values(%s);"""

with con.cursor() as cursor:
    cursor.execute(sql, ("加上点文字～～～～～！"))

con.commit()


sql_query = """select * from emoji;"""
with con.cursor() as cursor:
    cursor.execute(sql_query)
    result = cursor.fetchall()

pprint.pprint(result)


con.close()

