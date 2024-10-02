
from typing import (
    Dict,
)

import sys
import time
import argparse
from pathlib import Path

import pymysql

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def loadcfg(path: Path):
    with open(path, "rb") as f:
        return tomllib.load(f)


# 从一个查询中把字段头，和字段值，合并成一个字典。
def merge_header_value(cursor) -> Dict:
    fields = [i[0] for i in cursor.description]
    result = {}
    for k, v in zip(fields, cursor.fetchone()):
        result.update({k: v})

    return result


def show_replica_status(cursor) -> Dict:

    try:
        rows = cursor.execute("""show replica status;""")
    except pymysql.err.Error as e:
        print(e)
        print("查看 show replica status; 异常")
        sys.exit(1)

    print(f"{rows=} {cursor.fetchone()=}")
    print(f"{rows=} {cursor.fetchone()=}")
    if rows >= 1:
        return merge_header_value(cursor)
    else:
        print("没有 replica 信息")



def test():
    cfg = loadcfg(sys.argv[1])

    master = cfg["master"]

    conn = pymysql.connect(
                            host=master["host"],
                            port=master["port"],
                            user=master["user"],
                            password=master["password"],
                            )
    
    
    with conn.cursor() as cursor:
        show_replica_status(cursor)
    
    conn.close()


if __name__ == "__main__":
    test()


