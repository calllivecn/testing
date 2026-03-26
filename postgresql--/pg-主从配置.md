# postgresql 的主从配置


## 主库配置

- 1. 创建复制用户
    登录 psql，执行：
    ```sql
    CREATE ROLE replica LOGIN REPLICATION ENCRYPTED PASSWORD 'replica_password';
    ```

- 2. 配置 pg_hba.conf

    允许从库连接主库进行复制。在 pg_hba.conf 中添加：
    ```
    # TYPE  DATABASE        USER            ADDRESS           METHOD
    host    replication     replica         0.0.0.0/0         trust
    ```

- 3. 修改 postgresql.conf
    ```conf
    listen_addresses = '*'
    wal_level = replica          # 必须为replica或logical
    max_wal_senders = 10         # 最大流复制连接数
    wal_keep_size = 64GB # 我测试时没调整，默认为:0        # 避免从库因日志缺失断连，需根据磁盘空间调整
    ```

- 4. 重载配置:
    ```sql
    select pg_reload_conf(); # 如果成功会返回"t"
    ```

##  从库配置 

- 1. 停止从库服务并清理数据

    ```bash
    systemctl stop postgresql
    # 清空从库的数据目录，如 /var/lib/pgsql/data
    rm -rf /var/lib/pgsql/data/*
    ```

- 2. 执行基础备份 (pg_basebackup)
    使用 replica 用户同步主库数据：
    ```bash
    pg_basebackup -h 192.168.1.10 -U replica -D /var/lib/postgresql/data -Fp -P -R -CS "slot1"
    # -R 选项会自动在 data 目录创建 standby.signal 和 postgresql.auto.conf (含恢复信息)
    # -h: 主库IP, -U: 复制用户, -D: 数据目录, -P: 显示进度, -R: 自动生成从库配置
    ```

- 3. 确认并启动从库
    确认从库 data 目录下存在 standby.signal 文件。然后重启从库。


- 4. 验证主从同步

    在主库查看从库状态
    ```sql
    SELECT client_addr, state, sent_lsn, replay_lsn FROM pg_stat_replication;
    # 这行，说明正常
    state            | streaming
    ```

    在从库查看: ✅ 成功的标准：
    返回结果为 t (True)。
    如果返回 f (False)，说明它认为自己是主库，复制未生效。
    ```sql
    > SELECT pg_is_in_recovery();
     pg_is_in_recovery
    -------------------
     t 
    (1 行记录)

    ```

    进阶检查（查看接收和回放进度）：✅ 成功的标准：
    是否暂停 为 f。
    接收位置 和 回放位置 都在实时变化（说明数据正在源源不断地进来）。

    ```sql
    SELECT 
        pg_last_wal_receive_lsn() AS 接收位置, 
        pg_last_wal_replay_lsn() AS 回放位置,
        pg_is_wal_replay_paused() AS 是否暂停;
    ```



## 主从切换，手动：

- 1. 

- 在新主库上执行：

```sql
# SELECT pg_create_physical_replication_slot('slot1');
 pg_create_physical_replication_slot
-------------------------------------
 (slot1,)
(1 row)
```

