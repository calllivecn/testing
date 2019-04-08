#!/usr/bin/env python3
# coding=utf-8
# date 2019-04-04 11:32:21
# https://github.com/calllivecn

import sys
from pprint import pprint

import pymysql


try:
    conn = pymysql.Connect(host="172.32.1.2",
                            user="root",
                            password="mysql57",
                            db="mysql")
except pymysql.Error as e:
    print("连接错误")
    print(e)
    sys.exit(2)


slow_sql="""select avg(query_time) as avg_time,
                max(query_time) as max_time,
                min(query_time) as min_time,
                count(sql_text),sql_text,db 
                from slow_log 
                group by sql_text,db 
                order by avg_time desc 
                limit 10;"""


cursor = conn.cursor()

try:
    cursor.execute(slow_sql)
except pymysql.Error as e:
    pritn(e)
    sys.exit(3)

pprint(cursor.fetchall())

#conn.commit()

cursor.close()

conn.close()
