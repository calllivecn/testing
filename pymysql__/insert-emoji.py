#!/usr/bin/env python3
# coding=utf-8
# date 2018-12-24 10:21:55
# https://github.com/calllivecn

import pprint

import pymysql


#con = pymysql.connect(host="mysql.bnq.in",
#                        user="igor",
#                        password="123qwe",
#                        db="igor",
#                        #charset="utf8mb4",
#                        )

con = pymysql.connect(host="localhost",
                        port=13306,
                        user="root",
                        password="mysql5.7",
                        db="emoji",
                        #charset="utf8mb4",
                        )

sql = """insert into emoji(emoji) values(%s);"""

with con.cursor() as cursor:
    cursor.execute(sql, ("加上点文字～～～～～！😀😋"))

con.commit()


sql_query = """select * from emoji;"""
with con.cursor() as cursor:
    cursor.execute(sql_query)
    result = cursor.fetchall()

pprint.pprint(result)


con.close()

