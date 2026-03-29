#!/usr/bin/env python3
#coding=utf-8


import sqlite3 as sql

import sys

def out(lists):
    for f in lists:
        print(f)


db = sql.connect(sys.argv[1])


fetch = db.execute('select filename from sha group by filename having count(*)>1;')

multi_filename = fetch.fetchall()

out(multi_filename)


for f in multi_filename:
    f = f[0]
    fetch = db.execute('select * from sha where filename=? and size in (select size from (select size from sha where filename=?) group by size having count(*)>1);',(f,f))

    multi_size = fetch.fetchall()

    out(multi_size)

db.close()


