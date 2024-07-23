
import sys
import time
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
def create_replication():

    conn = pymysql.connect(
                            host=master["host"],
                            port=master["port"],
                            user=master["user"],
                            password=master["password"],
                            )
    
    
    cursor = conn.cursor()

    try:
        print("添加用户")
        #fetch = cursor.execute("""create user %s identified by %s;""", (replica["user"], replica["password"]))
        fetch = cursor.execute("""create user %s identified with 'mysql_native_password' by %s;""", (replica["user"], replica["password"]))
        print(f"{fetch=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("添加用户异常")
        sys.exit(1)


    try:
        print("用户授权")
        fetch = cursor.execute("""GRANT REPLICATION SLAVE ON *.* to %s@'%%';""", (replica["user"],))
        print(f"{fetch=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("用户授权异常")
        sys.exit(1)

    
    fetch = cursor.execute("""flush privileges;""")

    conn.close()



# 2. 从加上 添加 change master to ....
def ops_slave(slave):

    conn = pymysql.connect(
                            host=slave["host"],
                            port=slave["port"],
                            user=slave["user"],
                            password=slave["password"],
                            )
    
    
    cursor = conn.cursor()
    

    fetch = cursor.execute("""set global super_read_only=ON;""")

    try:
        print("config: change master to ... ")
        fetch = cursor.execute("""change master to master_host=%s,master_port=%s,master_user=%s,master_password=%s,master_auto_position=1;""", 
            (master["host"], int(master["port"]), replica["user"], replica["password"],)
            )

        fetch = cursor.execute("""start slave;""")

        print(f"{fetch=}, {cursor.fetchone()}")
    except pymysql.err.Error as e:
        print(e)
        print("config: change master to ... fail")
        sys.exit(1)


# 3. check slave
def check_slave_status(slave):

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
            fetch = cursor.execute("""show slave status;""")
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


Users = loadcfg("user-m-s.toml")

master = Users["master"]

replica = Users["replica"]

# 是list 可以有多个
slaves = Users["slaves"]


def main():
    create_replication()

    for slave in slaves:
        ops_slave(slave)
        check_slave_status(slave)
    

if __name__ == "__main__":
    main()
