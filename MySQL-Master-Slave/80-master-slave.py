
from typing import (
    Dict,
    Tuple,
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


def show_replica_status(cursor) -> Tuple[int, Dict]:

    try:
        rows = cursor.execute("""show replica status;""")
    except pymysql.err.Error as e:
        print(e)
        print("查看 show replica status; 异常")
        sys.exit(1)

    if rows >= 1:
        return rows, merge_header_value(cursor)
    else:
        # return 0, cursor.fetchone()
        return 0, None



# 1. 在主库上创建 repli_user 用户
def create_replication(master: Dict, replica: Dict, semi_sync: bool):

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
            print(f"""同步用户：{replica["user"]} 已经存在""")
        else:
            print("添加用户")
            # rows = cursor.execute("""create user %s identified by %s;""", (replica["user"], replica["password"]))
            rows = cursor.execute("""create user %s identified with 'mysql_native_password' by %s;""", (replica["user"], replica["password"]))
            print(f"{rows=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("添加用户异常")
        sys.exit(1)


    try:
        print("查询同步用户是否授权")
        rows = cursor.execute("""select Repl_slave_priv from mysql.user where user=%s and host='%%';""", (replica["user"],))
        result_char = cursor.fetchone()[0]
        if result_char == "Y":
            print(f"""用户：{replica["user"]} 已授权""")
        else:
            print("用户授权")
            rows = cursor.execute("""GRANT REPLICATION SLAVE ON *.* to %s@'%%';""", (replica["user"],))
            print(f"{rows=}, {cursor.fetchone()}")
            cursor.execute("""flush privileges;""")
    except pymysql.err.Error as e:
        print(e)
        sys.exit(1)
    

    # 半同步复制 master
    if semi_sync:
        print("设置半同步复制: source")
        try:
            cursor.execute("""install plugin rpl_semi_sync_source soname 'semisync_source.so';""")
            cursor.execute("""install plugin rpl_semi_sync_replica soname 'semisync_replica.so';""")
        except pymysql.err.Error as e:
            print(e)
            print("插件已经安装")
        
        cursor.execute("""set global rpl_semi_sync_source_enabled=1;""")

        print("根据你的场景，判断是否需要写入配置文件: 以下配置")
        print("rpl_semi_sync_source_enabled=1")

    conn.close()



# 2. check slave
def check_slave_status(slave: Dict, semi_sync: bool):

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
    
        rows, result = show_replica_status(cursor)

        print(f"检查中: {i}/{c} ...")
        # if result["Slave_IO_Running"] == "Yes" and result["Slave_SQL_Running"] == "Yes":
        if rows >= 1 and result["Replica_IO_Running"] == "Yes" and result["Replica_SQL_Running"] == "Yes":
            print("主从搭建成功")
            fail=False
            break
        else:
            time.sleep(5)
    
    if fail:
        print(f"主从搭建失败: {slave=}")
        sys.exit(1)
    

    # check 半同步
    if semi_sync:
        semi_sync_fail = False

        rows = cursor.execute("""show global variables like 'rpl_semi_sync_replica_enabled'""")
        field, result_char = cursor.fetchone()
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_replica_enabled = {result_char}")

        rows = cursor.execute("""show global status like 'rpl_semi_sync_replica_status'""")
        field, result_char = cursor.fetchone()
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_replica_status = {result_char}")

        
        if semi_sync_fail:
            print(f"开启半同步复制失败：{slave=}")
            sys.exit(1)

    conn.close()


# 3. 从加上 添加 change master to ....
def ops_slave(master: Dict, slave: Dict, replica: Dict, semi_sync: bool):

    conn = pymysql.connect(
                            host=slave["host"],
                            port=slave["port"],
                            user=slave["user"],
                            password=slave["password"],
                            )
    
    
    cursor = conn.cursor()

    replica_ok = False

    try:
        print("检测当前实例是否已 replica 到主库")
        rows, result = show_replica_status(cursor)

        if rows >= 1 and result["Replica_IO_Running"] == "Yes" and result["Replica_SQL_Running"] == "Yes":
            replica_ok = True
            print("replica 关系已存在，且状态正常")
        else:
            replica_ok = False
            print("配置: change replication source to ... ")
            # rows = cursor.execute("""change master to master_host=%s,master_port=%s,master_user=%s,master_password=%s,master_auto_position=1;""", 
            rows = cursor.execute("""change replication source to source_host=%s,source_port=%s,source_user=%s,source_password=%s,source_auto_position=1;""", 
                (master["host"], int(master["port"]), replica["user"], replica["password"],)
                )

            print(f"{rows=}, {cursor.fetchone()}")

    except pymysql.err.Error as e:
        print(e)
        print("配置: change replication source to ... 失败")
        sys.exit(1)
    
    if semi_sync:
        print("设置半同步复制: replica")
        try:
            cursor.execute("""install plugin rpl_semi_sync_source soname 'semisync_source.so';""")
            cursor.execute("""install plugin rpl_semi_sync_replica soname 'semisync_replica.so';""")
        except pymysql.err.Error as e:
            print(e)
            print("插件已经安装")

        cursor.execute("""set globaL rpl_semi_sync_replica_enabled=1;""")

        print("根据需要写入配置文件: 以下配置")
        print("rpl_semi_sync_replica_enabled=1")

        if replica_ok:
            cursor.execute("""stop replica;""")
            # cursor.execute("""reset replica;""")
        
        cursor.execute("""start replica;""")


    if not replica_ok:
        cursor.execute("""set global read_only=1;""")
        cursor.execute("""start replica;""")

    conn.close()



# 4. 检测主的半同步 
def check_master_semi_sync(master: Dict, semi_sync: bool):

    conn = pymysql.connect(
                            host=master["host"],
                            port=master["port"],
                            user=master["user"],
                            password=master["password"],
                            )
    
    
    cursor = conn.cursor()

    # check 半同步
    if semi_sync:
        semi_sync_fail = False

        rows = cursor.execute("""show global variables like 'rpl_semi_sync_source_enabled'""")
        field, result_char = cursor.fetchone()
        print(f"{field=} {result_char=}")

        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_source_enabled = {result_char}")

        
        rows = cursor.execute("""show global status like 'Rpl_semi_sync_source_status'""")
        field, result_char = cursor.fetchone()
        print(f"{field=} {result_char=}")
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_source_status = {result_char}")
        
        rows = cursor.execute("""show global status like 'Rpl_semi_sync_source_clients'""")
        field, result_int = cursor.fetchone()
        print(f"{field=} {result_int=}")
        if int(result_int) >= 1:
            pass
        else:
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_source_client = {result_char}")

        if semi_sync_fail:
            print(f"开启半同步复制失败：{master=}")
            sys.exit(1)


        print(f"开启半同步成功")
    
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

    parse.add_argument("cfg", nargs=1, type=loadcfg_toml, help="主从实例的配置信息")

    parse.add_argument("--semi-sync", dest="semi_sync", action="store_true", help="--semi-sync (添加半同步模式)")

    parse.add_argument("--parse", action="store_true", help=argparse.SUPPRESS)

    args = parse.parse_args()
    if args.parse:
        print(args)
        sys.exit(0)


    Users = args.cfg[0]

    master = Users["master"]

    replica = Users["replica"]

    # 是list 可以有多个
    slaves = Users["slaves"]


    create_replication(master, replica, args.semi_sync)

    for slave in slaves:
        ops_slave(master, slave, replica, args.semi_sync)
        check_slave_status(slave, args.semi_sync)
    
    check_master_semi_sync(master, args.semi_sync)

if __name__ == "__main__":
    main()
