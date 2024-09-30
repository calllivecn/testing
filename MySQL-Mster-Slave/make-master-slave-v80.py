
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
def merge_header_value(cursor) -> dict:
    fields = [i[0] for i in cursor.description]
    result = {}
    for k, v in zip(fields, cursor.fetchone()):
        result.update({k: v})

    return result


# 1. 在主库上创建 repli_user 用户
def create_replication(master: Dict, replica: Dict):

    conn = pymysql.connect(
                            host=master["host"],
                            port=master["port"],
                            user=master["user"],
                            password=master["password"],
                            )
    
    
    cursor = conn.cursor()

    try:
        print("查询同步用户是否存在")
        result = cursor.execute("""select user,host from mysql.user where user=%s;""", (replica["user"],))
        if result >= 1:
            print(f"""同步用户：{replica["user"]} 已经存在不用创建""")
        else:
            print("添加用户")
            #rows = cursor.execute("""create user %s identified by %s;""", (replica["user"], replica["password"]))
            rows = cursor.execute("""create user %s identified with 'mysql_native_password' by %s;""", (replica["user"], replica["password"]))
            print(f"{rows=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("添加用户异常")
        sys.exit(1)


    try:
        print("查询同步用户是否授权")
        result = cursor.execute("""SHOW GRANTS FOR %s@'%%';""", (replica["user"],))
        if result >= 1:
            print(f"""用户：{replica["user"]} 已授权""")
        else:
            print("用户授权")
            rows = cursor.execute("""GRANT REPLICATION SLAVE ON *.* to %s@'%%';""", (replica["user"],))
            print(f"{rows=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("用户授权异常")
        sys.exit(1)

    
    rows = cursor.execute("""flush privileges;""")

    conn.close()



# 2. 从加上 添加 change master to ....
def ops_slave(master: Dict, slave: Dict, replica: Dict):

    conn = pymysql.connect(
                            host=slave["host"],
                            port=slave["port"],
                            user=slave["user"],
                            password=slave["password"],
                            )
    
    
    cursor = conn.cursor()

    try:
        print("配置: change master to ... ")
        # v8.0.23 以后可以使用 change replication source to for channel 'channel_name'; 这种语句的
        # 也是从这版后，有了 MGR 集群模式。
        rows = cursor.execute("""change master to master_host=%s,master_port=%s,master_user=%s,master_password=%s,master_auto_position=1;""", 
            (master["host"], int(master["port"]), replica["user"], replica["password"],)
            )

        rows = cursor.execute("""start slave;""")

        print(f"{rows=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("配置: change master to ... 失败")
        sys.exit(1)

    #rows = cursor.execute("""set global super_read_only=ON;""")
    rows = cursor.execute("""set global read_only=ON;""")

    conn.close()



# 3. check slave
def check_slave_status(slave: Dict):

    conn = pymysql.connect(
                            host=slave["host"],
                            port=slave["port"],
                            user=slave["user"],
                            password=slave["password"],
                            )

    cursor = conn.cursor()
    
    c = 5
    fail = True
    for i in range(1, c+1):
    
        # check: show slave status;
        try:
            rows = cursor.execute("""show slave status;""")
        except pymysql.err.Error as e:
            print(e)
            print("用户授权异常")
            sys.exit(1)

        result = merge_header_value(cursor)

        print(f"检查中: {i}/{c} ...")
        if result["Slave_IO_Running"] == "Yes" and result["Slave_SQL_Running"] == "Yes":
            print("主从搭建成功")
            fail=False
            break
        else:
            time.sleep(5)
    
    if fail:
        print(f"主从搭建失败: {slave=}")
        sys.exit(1)

    conn.close()


def loadcfg_toml(cfg_name):
    p = Path(cfg_name)

    if p.exists():
        try:
            r = loadcfg(p)
        except Exception:
            argparse.ArgumentTypeError(f"需要是 toml 配置文件")
        
        return r

    else:
        argparse.ArgumentTypeError(f"需要给出一个 toml 配置文件")


def main():
    parse = argparse.ArgumentParser(
        usage="%(prog)s --help 查看使用说明",
        description="创建mysql 8.0 的一主从一从 OR 一主多从",
        )

    parse.add_argument("cfg", nargs="1", type=loadcfg_toml, help="主从实例的配置信息")

    parse.add_argument("--semi-sync", dest="semi_sync", action="store_true", help="可选的--semi-sync (使用半同步模式创建)")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()
    if args.parse:
        print(parse)
        sys.exit(0)


    Users = args.cfg

    master = Users["master"]

    replica = Users["replica"]

    # 是list 可以有多个
    slaves = Users["slaves"]


    create_replication(master, replica=replica)

    for slave in slaves:
        ops_slave(master, slave, replica)
        check_slave_status(slave)
    

if __name__ == "__main__":
    main()
