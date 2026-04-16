# 测试使用postgresql

- 安装: pip install psycopg[binary,pool]

- SQLAlchemy (ORM 方案)

### 如果你不希望直接编写原始 SQL，而是想用 Python 对象来操作数据库，SQLAlchemy 是首选。它底层通常也是调用 psycopg。

```Python
from sqlalchemy import create_engine
# 使用 psycopg3 作为驱动
engine = create_engine("postgresql+psycopg://user:pass@localhost/dbname")
```

## 生成测试使用数据

- pip install faker

## 官方推荐的 GUI的客户端

- https://www.pgadmin.org/
- 容器名: docker.io/dpage/pgadmin4:latest



## 使用+查看+运维

- 查看当前使用的数据目录：SHOW data_directory;
- 不想登录进 psql 交互界面，可以直接在终端运行：psql -t -c "SHOW data_directory;"


## pgpool-II 容器

- podman build -f Dockerfile-pgpool-ii -t pgpool2 .



# 常见集群架构介绍

PostgreSQL 的“集群”概念通常可以分为两种语境：一种是**单机实例内的逻辑集群**（Database Cluster），另一种是用于高可用或负载均衡的**多机架构集群**。

在生产环境下，大家通常讨论的是后者。以下是 PostgreSQL 常见的几种多机集群模式及其区别：

---

## 1. 主从流复制 (Streaming Replication)
这是 PostgreSQL 最官方、最常用的方案。它通过传输 WAL（Write Ahead Log）日志来实现数据同步。

* **架构类型：** 一主多从 (Single Master, Multiple Replicas)。
* **同步方式：** * **异步复制：** 性能高，但主库宕机时可能会有少量数据丢失。
    * **同步复制：** 确保数据零丢失，但如果从库响应慢，会影响主库的写入性能。
* **特点：** * 主库负责读写，从库只读（Hot Standby）。
    * 通常配合 **Patroni + Etcd/Consul** 来实现自动故障转移（Failover）。

---

## 2. 逻辑复制 (Logical Replication)
基于逻辑解析 WAL 日志，允许在表级别进行细粒度的同步。

* **架构类型：** 发布/订阅模式 (Pub/Sub)。
* **区别于流复制：** * 流复制是物理层的“全盘拷贝”，逻辑复制可以选择只同步特定的表。
    * 支持**跨版本**复制（例如从 PostgreSQL 12 同步到 16）。
    * 支持在目标端对数据进行转换或触发器处理。
* **应用场景：** 数据迁移、数据集成、构建报表库。

---

## 3. 读写分离集群 (Read-Write Splitting)
这通常不是一种数据库内核技术，而是一种**架构设计**，通过代理层实现。

* **关键组件：** **Pgpool-II** 或 **HAProxy**。
* **区别：** * 代理层会自动将 `SELECT` 请求分发到从库，将 `INSERT/UPDATE` 请求发送到主库。
    * 对于应用层透明，开发者不需要在代码里手动切换数据源。

---

## 4. 逻辑多主集群 (Multi-Master Replication)
允许在多个节点上同时进行读写操作。

* **典型方案：** **BDR (Bi-Directional Replication)**。
* **特点：** * 解决跨地域的写入延迟问题。
    * **复杂性：** 必须处理冲突解决（例如两个节点同时修改同一行）。
    * 由于维护成本和冲突风险极高，通常只在特定业务场景下使用。

---

## 5. 分布式分片集群 (Sharding/Horizontal Scaling)
将数据水平切分（Sharding）到不同的物理节点上，解决单机存储瓶颈。

* **典型方案：** **Citus**（PostgreSQL 的插件化扩展）。
* **架构：** 一个协调节点 (Coordinator) + 多个工作节点 (Worker)。
* **区别：** * 它将大表拆分成多个分片（Shards）分布在不同机器。
    * 适合 **PB 级别** 的超大规模数据处理（HTAP 场景）。

---

## 核心区别总结表

| 模式 | 核心目标 | 写入能力 | 数据一致性 | 复杂度 |
| :--- | :--- | :--- | :--- | :--- |
| **流复制 (Physical)** | 高可用 (HA) | 仅单节点 | 强一致/最终一致 | 低 |
| **逻辑复制** | 数据集成/跨版本 | 仅单节点 | 最终一致 | 中 |
| **Citus (Sharding)** | 水平扩展 (Scale-out) | 多节点并行 | 强一致 | 高 |
| **BDR (Multi-Master)** | 多地写入 | 全节点 | 冲突合并/最终一致 | 极高 |

---

### 给高级用户的建议
如果你是在生产环境中搭建，最稳健的选择是 **流复制 + Patroni**。如果你面临的是海量数据查询性能问题，则应该考虑 **Citus**。

由于你熟悉 Python 和 Bash，可以尝试使用 `ansible` 或 `patroni-ansible` 来快速部署一套高可用集群。

```python
# 示例：通过 Python 检查主从状态 (psycopg2)
import psycopg2

def get_recovery_status(conn_params):
    with psycopg2.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # 返回 True 表示是从库（处于恢复模式），False 表示是主库
            cur.execute("SELECT pg_is_in_recovery();")
            return cur.fetchone()[0]
```

你需要针对具体的业务场景（是追求高可用，还是追求水平扩展）来选择吗？
