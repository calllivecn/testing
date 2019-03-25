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
                        password="mysql57",
                        #db="zhangxu",
                        )
except pymysql.err.Error as e:
    print("连接异常")
    exit(1)

host="%"
username = "python3"
password = "zxpython"

useradd = """create user "{}"@"{}" identified by "{}";"""
useradd_up = """create user %s@%s identified by %s;"""
userdel_up = """drop user %s@%s;"""
showuser_up = """show grants for %s@%s;"""
flush_privileges = """flush privileges;"""

grant_up = """grant all on {}.* to "{}"@"{}";"""
db = "db1"

cursor = con.cursor()

try:
    result = cursor.execute(useradd_up, (username, host, password))
    print(result)
    print(cursor.fetchone())
except pymysql.err.Error as e:
    print(e)
    print("添加用户异常")
    exit(1)

try:
    result = cursor.execute(grant_up.format(db, username, host))
    print(result)
    print(cursor.fetchone())
except pymysql.err.Error as e:
    print(e)
    print("用户授权异常")
    exit(1)


try:
    result = cursor.execute(showuser_up, (username, host))
    print(result)
    print(cursor.fetchone())
except pymysql.err.Error as e:
    print(e)
    print("查看用户异常")
    exit(1)

def delete():
    try:
        result = cursor.execute(userdel_up,(username, host))
        print(result)
        print(cursor.fetchone())
    except pymysql.err.Error as e:
        print(e)
        print("删除用户异常")
        exit(1)


print("show user info")
result = cursor.execute(flush_privileges)
print(cursor.fetchone())

con.commit()

cursor.close()

con.close()
