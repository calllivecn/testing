## 在 PostgreSQL 17 中，主从切换（Failover）通常发生在主库故障，需要将从库提升为新的主库时。整个过程可以分为三个主要阶段：**提升备库**、**更新应用连接**以及**恢复原主库**。

以下是一套详细的手动切换操作步骤。

### 🚀 第一阶段：提升备库为新主库

当确认原主库已不可用时，需要在备库上执行提升操作。

1.  **检查备库状态**
    在提升前，建议先检查备库的复制延迟，以评估可能丢失的数据量。在备库上执行：

    ```sql
    -- 检查备库是否处于恢复模式（应返回 't'）
    SELECT pg_is_in_recovery();

    -- 检查复制延迟（单位：秒）
    SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
    ```

	### pg_last_xact_replay_timestamp(): 获取从库最近一次重放（应用）事务的时间戳。这个时间戳是该事务在主库（Primary）上提交时的原始时间。如果主库现在完全没有写入操作（处于空闲状态），pg_last_xact_replay_timestamp 会停留在最后一个事务发生的时间。随着 now() 不断增加，你会发现 replication_delay 的数值在不断变大。


2.  **执行提升命令**
    有两种常用方法可以将备库提升为主库，任选其一即可。

    *   **方法一：使用 `pg_ctl` 命令（推荐）**
        在操作系统命令行中，以 `postgres` 用户执行：
        ```bash
        pg_ctl promote -D $PGDATA
        ```
    *   **方法二：使用 SQL 函数**
        在备库的 `psql` 终端中执行：
        ```sql
        SELECT pg_promote();
        ```

3.  **验证提升结果**
    提升操作完成后，需要验证备库是否已成功变为主库。
    ```sql
    -- 再次检查，此时应返回 'f'，表示不再处于恢复模式
    SELECT pg_is_in_recovery();

    -- 尝试创建一个测试表，验证写入权限
    CREATE TABLE failover_test (id int);
    DROP TABLE failover_test;
    ```
    如果 `pg_is_in_recovery()` 返回 `f` 且能成功执行写入操作，说明提升成功。

### 🔗 第二阶段：更新应用程序连接

备库提升后，应用程序需要连接到这个新的主库。

*   **修改连接配置**：更新应用程序的数据库连接字符串，将主机地址指向新主库的 IP 地址。
*   **使用负载均衡/代理**：如果使用了 HAProxy、Pgpool-II 等中间件，需要更新其配置，将写请求路由到新的主库，然后重载服务。
    ```bash
    # 示例：重载 HAProxy 配置
    sudo systemctl reload haproxy
    ```

### 🔄 第三阶段：恢复原主库并重新接入集群（可选）

当原主库的故障被修复后，可以将其重新配置为新主库的备库。这里有两种方案可供选择。

#### 方案 A：使用 `pg_basebackup` 重新同步（简单可靠）

此方法会清空原主库的所有数据，并从新主库进行一次全量数据同步。适用于数据量不大或对停机时间不敏感的场景。

1.  **停止原主库服务**
    ```bash
    pg_ctl stop -D $PGDATA
    ```
2.  **备份或清空原数据目录**
    为避免数据混乱，建议先备份或重命名原数据目录。
    ```bash
    mv $PGDATA $PGDATA_old
    ```
3.  **从新主库拉取数据**
    使用 `pg_basebackup` 工具从新主库（假设IP为 `192.168.100.171`）同步数据。
    ```bash
    pg_basebackup -h 192.168.100.171 -p 5432 -U postgres -D $PGDATA -Fp -P -Xs -R -v
    ```
    *   `-R` 参数会自动创建 `standby.signal` 文件并配置 `primary_conninfo`，简化了后续步骤。
4.  **启动数据库服务**
    ```bash
    pg_ctl start -D $PGDATA
    ```
5.  **验证同步状态**
    在新主库上查询 `pg_stat_replication` 视图，确认原主库已作为备库连接并开始同步。
    ```sql
    SELECT pid, state, client_addr, sync_state FROM pg_stat_replication;
    ```

#### 方案 B：使用 `pg_rewind` 工具（快速高效）

此方法通过回放 WAL 日志来使原主库的数据目录与新主库保持一致，速度更快，但需要提前配置。

1.  **检查前提条件**
    此方法要求数据库的 `wal_log_hints` 参数必须为 `on`, 如果开启了`show data_checksums` 为 `on`那wal_log_hints 也有强制开启了，不论它的值是否为on。 （`full_page_writes` 默认为 `on`）。
    ```sql
    SHOW wal_log_hints;
    SHOW full_page_writes;
    ```
    如果 `wal_log_hints` 为 `off`，需要修改配置文件并重启数据库才能生效。
    
    关于: data_checksums 的配置方式比较特殊: 它的配置取决于你的数据库处于哪个阶段：是新建集群，还是已有集群。

    A. 新建集群（初始化阶段）

    如果你正在部署一个新的 PostgreSQL 实例，需要在初始化数据目录时通过命令行参数开启。
    命令：initdb 参数：-k 或 --data-checksums

    ```bash
    # 示例：初始化一个带数据校验的新集群
    initdb -D /usr/local/pgsql/data --data-checksums
    注意：从 PostgreSQL 18 开始，data_checksums 变为默认开启。但在 PG 17 及之前的版本中，必须手动加参数。
    ```

    B. 已有集群（运行中阶段）

    如果数据库已经运行且未开启校验，你无法通过修改配置文件开启。必须使用专门的工具 pg_checksums 进行“离线”转换。
    这是一个重操作，需要停机。

    🛑 操作步骤：
    停止数据库服务
    ```bash
    pg_ctl stop -D /path/to/data
    ```
    执行开启命令
    使用 pg_checksums 工具扫描所有数据文件并计算校验和，然后更新控制文件。
    ```bash
    # --enable: 开启校验
    # -D: 指定数据目录
    # -P: 显示进度 (Progress)
    pg_checksums --enable -D /path/to/data -P
    ```

    启动数据库服务
    ```bash
    pg_ctl start -D /path/to/data
    ```

    验证状态: 登录数据库查询参数确认是否生效：
    
    ```sql
    SHOW data_checksums;
    -- 输出应为: on
    ```

    C. 核心注意事项（必读）
    
    在执行上述操作前，请务必了解以下影响：

    | 关注点 | 说明 |
    | :--- | :--- |
    | 停机时间 | 开启过程必须停机。对于大数据量的库，扫描和计算校验和可能需要很长时间（取决于磁盘 I/O 和数据量）。 |
    | 不可逆性 | 一旦开启，无法直接关闭。虽然 `pg_checksums` 工具提供了 `--disable` 选项，但通常不建议在生产环境这么做，除非是为了排查故障。 |
    | 性能损耗 | 开启后会带来轻微的 CPU 和 I/O 开销（通常在 5% 左右），因为每次读写数据页都要计算校验值。 |
    | 高可用方案 | 如果无法接受长时间停机，可以在备库（Standby）上先执行上述操作（停备库 -> 开启校验 -> 起备库），然后进行主从切换，再处理旧主库。 |

2.  **停止原主库服务**
    ```bash
    pg_ctl stop -D $PGDATA
    ```

3.  **执行 `pg_rewind`**
    使用 `pg_rewind` 工具将原主库的数据目录与新主库同步。
    ```bash
    pg_rewind --target-pgdata $PGDATA --source-server='host=192.168.100.171 port=5432 user=postgres dbname=postgres'
    ```

4.  **配置为新备库**
    如果 `pg_basebackup` 没有使用 `-R` 参数，需要手动配置。

* 在 `$PGDATA/postgresql.auto.conf` 文件中添加或修改 `primary_conninfo` 参数，指向新主库。
    
    ```
    primary_conninfo = 'user=postgres password=your_password host=192.168.100.171 port=5432'
    ```

* 创建 `standby.signal` 文件（PostgreSQL 12+）。
    ```bash
    touch $PGDATA/standby.signal
    ```

5.  **启动数据库服务**
    ```bash
    pg_ctl start -D $PGDATA
    ```

6.  **验证同步状态**
    同样，在新主库上查询 `pg_stat_replication` 确认同步已建立。

### ✨ 补充说明：自动故障切换

除了手动操作，生产环境中更推荐使用 Patroni、repmgr 等高可用管理工具来实现自动故障检测和切换，可以最大程度减少停机时间和人工干预。
