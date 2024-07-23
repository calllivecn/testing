#!/usr/bin/env python3
# coding=utf-8
# date 2018-12-24 17:04:46
# https://github.com/calllivecn



from pprint import pprint

import pymysql


from user import Users

dbinfo = Users["mysql"][0]

con = pymysql.connect(
                        host=dbinfo["host"],
                        port=dbinfo["port"],
                        user=dbinfo["user"],
                        password=dbinfo["password"],
                        database=dbinfo["db"],
                        # charset=dbinfo.charset,
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


