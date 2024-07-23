#!/usr/bin/env python3
# coding=utf-8
# date 2019-01-25 14:00:34
# https://github.com/calllivecn

import sys
from pprint import pprint

import pymysql

from user import Users

dbinfo = Users["mysql"][0]

try:
    conn = pymysql.connect(
                        host=dbinfo["host"],
                        port=dbinfo["port"],
                        user=dbinfo["user"],
                        password=dbinfo["password"],
                        )

except pymysql.err.Error as e:
    print(f"连接异常: {e}")
    sys.exit(1)

useradd = """create user %s@%s identified by %s;"""
userdel = """drop user %s@%s;"""
showuser = """show grants for %s@%s;"""
flush_privileges = """flush privileges;"""

#grant = """grant all on {}.* to "{}"@"{}";"""
# 使用不了占位符？！？！, 不是 db.* 这里有特殊。
grant_up = """grant all privileges on *.* to %s@%s;"""

with conn.cursor() as cursor:
    try:
        print("添加用户...")
        result = cursor.execute(useradd, (username, host, password))
        print("添加用户... ok")
        print(f"{result}, {cursor.fetchone()}")
    
        print("用户授权...")
        sql = cursor.mogrify(grant_up, (username, host))
        print(f"{sql=}")
        result = cursor.execute(grant_up, (username, host))
        print("用户授权... ok")
        print(f"{result}, {cursor.fetchone()}")

        print("查看用户...")
        result = cursor.execute(showuser, (username, host))
        print("查看用户... ok")
        print(f"{result}, {cursor.fetchone()}")

    #except pymysql.err.Error as e:
    except Exception as e:
        print(e)
        sys.exit(1)


def delete():
    try:
        result = cursor.execute(userdel, (username, host))
        print(f"{result=}, {cursor.fetchone()=}")
    except pymysql.err.Error as e:
        print(e)
        sys.exit(1)


conn.close()
