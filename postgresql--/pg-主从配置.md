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
    pg_basebackup -h 192.168.1.10 -U replica -D /var/lib/postgresql/data -Fp -P -R -C -S "slot1"
    # -R 选项会自动在 data 目录创建 standby.signal 和 postgresql.auto.conf (含恢复信息)
    -- or ---
    # -h: 主库IP, -U: 复制用户, -D: 数据目录, -P: 显示进度, -R: 自动生成从库配置
    sudo -u postgres pg_basebackup -h 192.168.1.10 -U replica_user -D /var/lib/postgresql/data/ -Fp -Xs -P -R
    ```

- 3. 确认并启动从库
    确认从库 data 目录下存在 standby.signal 文件。然后重启从库。


- 4. 四、 验证主从同步
    在主库查看从库状态
    ```sql
    select * from pg_stat_replication;
    # 这行，说明正常
    state            | streaming
    ```
