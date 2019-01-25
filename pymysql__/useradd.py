#!/usr/bin/env python3
# coding=utf-8
# date 2019-01-25 14:00:34
# https://github.com/calllivecn

from pprint import pprint

import pymysql

try:
    con = pymysql.connect(
                        host="localhost",
                        port=13306,
                        #user="zhangxu",
                        user="root",
                        password="zxmysql",
                        #db="zhangxu",
                        )
except pymysql.err.Error as e:
    print(e)
    print("连接异常")
    exit(1)

host="%"
username = "python3"
password = "zxpython"

useradd = """create user "{}"@"{}" identified by "{}";"""
userdel = """drop user {};"""
showuser = """show grants for {};"""
flush_privileges = """flush privileges;"""

grant = """grant {} on {}.{} to {}@{};"""

cursor = con.cursor()

sql = useradd.format(username, host, password)
try:
    result = cursor.execute(sql)
    print(result)
except pymysql.err.Error as e:
    print(e)
    print("添加用户异常")
    exit(1)

try:
    resutl = cursor.execute(showuser.format(username))
    print(result)
except pymysql.err.Error as e:
    print(e)
    print("查看用户异常")
    exit(1)

con.commit()

cursor.close()

con.close()
