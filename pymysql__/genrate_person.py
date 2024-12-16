#!/usr/bin/env python3
# coding=utf-8
# date 2024-12-16 13:42:34
# author calllivecn <calllivecn@outlook.com>

import sys
import random
from datetime import (
    date,
    datetime,
)

import pymysql

from mimesis import (
    Address,
    Person,
)
from mimesis.locales import Locale

from user import Users

# 计算age
def age(now, birth) -> int:
    delta = now - birth
    return round(delta.days / 365.25)


def random_person(count=10000):
    zh = Person(locale=Locale.ZH)
    now = datetime.now()
    now = date(now.year, now.month, now.day)
    data = []
    for i in range(count):
        birthdate = zh.birthdate()
        d = (
                zh.username(), # varchar(128)
                zh.password(), # varchar(32)
                f"{zh.surname()}{zh.name()}", # varchar(64)
                zh.sex(), # 性别 varchar(6)
                age(now, birthdate), # tinyint
                str(birthdate), # 日生 char(10)
                zh.blood_type(), # 血型 chat(8)
                zh.email(), # varchar(128)
                float(zh.height()), #  身高, float
                float(zh.weight()), # 体重 float()
                zh.occupation(), # 职业 varchar(128)
                zh.phone_number(), # varchar(128)
                zh.university() # 毕业学校, varchar(64)
                )

        data.append(d)

    #print(data[0])
    return data


def main():

    create_db = """create database if not exists test;"""

    create_table = """\
        create table if not exists t_person(
            id bigint primary key auto_increment,
            username varchar(128) not null,
            password varchar(32) not null,
            name varchar(64),
            sex varchar(6),
            age tinyint, 
            birthdate char(10),
            blood_type char(8),
            email varchar(128),
            height float comment '身高单位：米',
            weight float comment '体重单位：千克',
            occupation varchar(128),
            phone_number varchar(128),
            university varchar(128)
        );
        """


    dbinfo = Users["mysql"][0]

    conn = pymysql.connect(
            host=dbinfo["host"],
            port=dbinfo["port"],
            user=dbinfo["user"],
            password=dbinfo["password"],
            )

    cursor = conn.cursor()
    cursor.execute(create_db)
    conn.select_db("test")
    cursor.execute(create_table)
    insert_sql = """\
        insert into t_person(
            username,
            password,
            name,
            sex,
            age,
            birthdate,
            blood_type,
            email,
            height,
            weight,
            occupation,
            phone_number,
            university
        )
        values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

    c = 0
    for i in range(1, int(sys.argv[1])+1):
        conn.begin()
        result = cursor.executemany(insert_sql, random_person())
        conn.commit()
        print(f"已经写入{i}万条了")

    conn.close()


if __name__ == "__main__":
    main()
