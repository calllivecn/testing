
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
            print(f"""同步用户：{replica["user"]} 已经存在不用创建""")
        else:
            print("添加用户")
            #rows = cursor.execute("""create user %s identified by %s;""", (replica["user"], replica["password"]))
            # ~~8.0 之前的， 在配置中文中设置默认认证插件为 default_authentication_plugin=caching_sha2_password 就行.~~
            # ~~不然就在在创建用户时指定 'mysql_native_password'~~ 这种不行
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
    except pymysql.err.Error as e:
        print(e)
        sys.exit(1)

    
    rows = cursor.execute("""flush privileges;""")


    # 半同步复制 master
    if semi_sync:
        print("设置半同步复制: master")
        try:
            cursor.execute("""INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';""")
            cursor.execute("""set global rpl_semi_sync_master_enabled=1;""")
        except pymysql.err.Error as e:
            print(e)
            sys.exit(1)
        
        print("根据你的场景，判断是否需要写入配置文件: 以下配置")
        print("rpl_semi_sync_master_enabled=ON")

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
    
        # check: show slave status;
        try:
            rows = cursor.execute("""show slave status;""")
        except pymysql.err.Error as e:
            print(e)
            print("查看 show replica status; 异常")
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
    

    # check 半同步
    if semi_sync:
        semi_sync_fail = False

        rows = cursor.execute("""show global variables like 'rpl_semi_sync_slave_enabled'""")
        field, result_char = cursor.fetchone()
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_slave_enabled = {result_char}")

        rows = cursor.execute("""show global status like 'rpl_semi_sync_slave_status'""")
        field, result_char = cursor.fetchone()
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_slave_status = {result_char}")


        
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

    try:
        print("配置: change master to ... ")
        # v8.0.23 以后可以使用 change replication source to for channel 'channel_name'; 这种语句的
        # 也是从这版后，有了 MGR 集群模式。
        rows = cursor.execute("""change master to master_host=%s,master_port=%s,master_user=%s,master_password=%s,master_auto_position=1;""", 
            (master["host"], int(master["port"]), replica["user"], replica["password"],)
            )

        print(f"{rows=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("配置: change master to ... 失败")
        sys.exit(1)
    
    if semi_sync:
        print("设置半同步复制: slave")
        try:
            rows = cursor.execute("""INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';""")
            rows = cursor.execute("""SET GLOBAL rpl_semi_sync_slave_enabled=1;""")
        except pymysql.err.Error as e:
            print(e)
            print("配置: change master to ... 失败")
            sys.exit(1)

        print("根据你的场景，判断是否需要写入配置文件: 以下配置")
        print("rpl_semi_sync_slave_enabled=ON")


    #rows = cursor.execute("""set global super_read_only=ON;""")
    rows = cursor.execute("""set global read_only=ON;""")


    rows = cursor.execute("""start slave;""")

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

        rows = cursor.execute("""show global variables like 'rpl_semi_sync_master_enabled'""")
        field, result_char = cursor.fetchone()
        print(f"{field=} {result_char=}")

        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_master_enabled = {result_char}")

        
        rows = cursor.execute("""show global status like 'Rpl_semi_sync_master_status'""")
        field, result_char = cursor.fetchone()
        print(f"{field=} {result_char=}")
        if result_char != "ON":
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_master_status = {result_char}")
        
        rows = cursor.execute("""show global status like 'Rpl_semi_sync_master_clients'""")
        field, result_int = cursor.fetchone()
        print(f"{field=} {result_int=}")
        if int(result_int) >= 1:
            pass
        else:
            semi_sync_fail = True
            print(f"配置失败：")
            print(f"rpl_semi_sync_master_client = {result_char}")

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
        description="创建mysql 5.7 的一主从一从 OR 一主多从",
        )

    parse.add_argument("cfg", nargs=1, type=loadcfg_toml, help="主从实例的配置信息")

    parse.add_argument("--semi-sync", dest="semi_sync", action="store_true", help="可选的--semi-sync (半同步模式创建)")

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
