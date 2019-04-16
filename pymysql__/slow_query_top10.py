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


slow_sql="""
select avg(time_to_sec(query_time)) as avg_time,
max(query_time) as max_time,
min(query_time) as min_time,
sum(query_time) as sum_time,
count(*),sql_text,db 
from slow_log1 
group by sql_text,db 
order by sum_time desc 
limit 10;
"""

roll_poling=[
# use mysql;

"drop table if exists slow_log3;",

# 清理一下，防止重名。
"drop table if exists slow_log_tmp;",

"create table if not exists slow_log_tmp like slow_log;",
"create table if not exists slow_log1 like slow_log;",
"create table if not exists slow_log2 like slow_log;",

"rename table slow_log2 to slow_log3;",
"rename table slow_log1 to slow_log2;",

"set @old_log_state=@@GLOBAL.slow_query_log;",
"set GLOBAL slow_query_log=0;",

"rename table slow_log to slow_log1, slow_log_tmp to slow_log;",

"set GLOBAL slow_query_log=@old_log_state;",
]

# slow_log 回退
backspace = [
        "create table if not exists slow_log1 like slow_log;",
        "create table if not exists slow_log2 like slow_log;",
        "create table if not exists slow_log3 like slow_log;",

        "set @old_log_state=@@GLOBAL.slow_query_log;",
        "set GLOBAL slow_query_log=0;",

        "drop table if exists slow_log;",
        "rename table slow_log1 to slow_log;",

        "set GLOBAL slow_query_log=@old_log_state;",

        "rename table slow_log2 to slow_log1;",
        "rename table slow_log3 to slow_log2;",

        ]

cursor = conn.cursor()

try:
    for sql in roll_poling:
        cursor.execute(sql)
except pymysql.Error as e:
    print(e)
    sys.exit(3)


yesno = input("是否回退? [n/Y]")
if yesno == "y" or yesno == "Y" or yesno == "":
    print("执行回退.")
    try:
        for sql in backspace:
            cursor.execute(sql)
    except pymysql.Error as e:
        print("slow_log 回退出错。")
        print(e)
        sys.exit(4)
else:
    print("不执行回退.")


try:
    cursor.execute(slow_sql)
except pymysql.Error as e:
    print(e)
    sys.exit(3)


for info in cursor.fetchall():
    print("原信息：",info)
    for i in info:
        print(str(i), "-- ", end="")
    print()

#conn.commit()

cursor.close()

conn.close()
