
基于你现有的 PostgreSQL 两节点主从流复制架构，要实现负载均衡（BL）和高可用（HA），最核心的方案是引入 **pgpool-II** 作为中间件，并启用其 **Watchdog（看门狗）** 功能。

由于你只有两个数据库节点，为了保证整个架构没有单点故障，建议部署 **两个 pgpool-II 节点**（通常与数据库节点混部或独立部署），形成“双活”或“主备”模式。

以下是完整的配置流程：

### 🏗️ 架构规划

在开始之前，请确认你的 IP 规划。假设环境如下：

| 角色 | 节点 1 (Server 1) | 节点 2 (Server 2) | 虚拟 IP (VIP) |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | Primary (主)IP: 192.168.1.101 | Standby (从)IP: 192.168.1.102 | - |
| **Pgpool-II** | Active (主)IP: 192.168.1.101 | Standby (备)IP: 192.168.1.102 | **192.168.1.200** |

*   **VIP (192.168.1.200)**：应用程序连接数据库的地址。
*   **端口**：PostgreSQL 默认 5432，Pgpool-II 默认 9999。

---

### 🛠️ 第一阶段：PostgreSQL 数据库层准备

在配置 Pgpool 之前，必须确保数据库层已经准备好接受 Pgpool 的监控和连接。

#### 1. 创建专用用户
在 **Primary** 节点上执行，用于 Pgpool 的健康检查和复制延迟检查。

```sql
-- 登录数据库
psql -U postgres

-- 创建复制用户 (用于流复制)
CREATE ROLE repl WITH REPLICATION LOGIN PASSWORD 'repl_password';

-- 创建监控用户 (用于 Pgpool 健康检查)
CREATE ROLE pgpool WITH LOGIN PASSWORD 'pgpool_password';

-- 赋予监控权限 (Pgpool-II 4.1+ 推荐，用于显示复制状态)
GRANT pg_monitor TO pgpool;
```

#### 2. 配置 pg_hba.conf
在 **Primary** 和 **Standby** 节点的 `pg_hba.conf` 中添加信任规则，允许 Pgpool 节点连接。

```text
# 允许复制连接
host    replication     repl            192.168.1.0/24        scram-sha-256 (或 md5)
# 允许监控用户连接
host    all             pgpool          192.168.1.0/24        scram-sha-256 (或 md5)
# 允许业务用户连接
host    all             all             192.168.1.0/24        scram-sha-256 (或 md5)
```
*配置后记得重载配置：`SELECT pg_reload_conf();`*

#### 3. 配置 SSH 免密登录 (关键)
Pgpool-II 的自动故障转移和在线恢复功能依赖 SSH。
*   **操作**：在所有节点上，使用 `postgres` 用户生成 SSH 密钥，并将公钥分发到所有节点（包括自己）。
*   **验证**：`ssh postgres@192.168.1.101` 和 `ssh postgres@192.168.1.102` 均无需密码。

---

### ⚙️ 第二阶段：Pgpool-II 安装与基础配置

在 **两个节点** 上安装 pgpool-II。

#### 1. 生成密码文件 (pool_passwd)
Pgpool-II 使用自己的密码文件。在 **任意一个节点** 生成后，同步到另一个节点。

```bash
# 生成 md5 加密的密码文件
pg_md5 pgpool_password  # 输入密码后生成 md5 串
pg_md5 postgres_password # 获取 postgres 的 md5 串

# 编辑 /etc/pgpool-II/pool_passwd (路径视安装方式而定)
# 格式：用户名:md5加密串
postgres:md5xxxxxxxxxx
pgpool:md5xxxxxxxxxx
```

#### 2. 配置 pgpool.conf (核心)
这是最关键的一步。你需要修改 `/etc/pgpool-II/pgpool.conf`。以下配置需在 **两个节点** 上保持一致（除了 `wd_hostname`）。

**A. 基础连接设置**
```ini
listen_addresses = '*'
port = 9999
pcp_port = 9898
```

**B. 后端节点定义 (Backend Nodes)**
```ini
# 节点 0 (Primary)
backend_hostname0 = '192.168.1.101'
backend_port0 = 5432
backend_weight0 = 1
backend_data_directory0 = '/var/lib/pgsql/data' # 你的PG数据目录
backend_flag0 = 'ALLOW_TO_FAILOVER'

# 节点 1 (Standby)
backend_hostname1 = '192.168.1.102'
backend_port1 = 5432
backend_weight1 = 1
backend_data_directory1 = '/var/lib/pgsql/data'
backend_flag1 = 'ALLOW_TO_FAILOVER'
```

**C. 健康检查与复制延迟检查**
```ini
# 健康检查周期（秒）
health_check_period = 10
health_check_timeout = 20
health_check_user = 'pgpool'
health_check_password = 'pgpool_password'
health_check_database = 'postgres'

# 复制延迟检查
sr_check_period = 5
sr_check_user = 'pgpool'
sr_check_password = 'pgpool_password'
# 延迟阈值（字节），超过此值暂停负载均衡，强制读主库
delay_threshold = 10000000 
```

**D. 读写分离配置**
```ini
# 开启负载均衡
load_balance_mode = on
# 定义哪些语句走从库 (默认 SELECT)
white_function_list = ''
black_function_list = 'nextval, setval' # 序列函数不走从库
```

**E. 看门狗配置 (HA 核心)**
这是实现 BL+HA 的关键，确保 VIP 在节点间漂移。

```ini
use_watchdog = on

# --- 节点 1 特有配置 ---
# 本机看门狗主机名
wd_hostname = '192.168.1.101' 
# 虚拟 IP (VIP)
delegate_IP = '192.168.1.200'
# 绑定网卡 (根据实际网卡名修改，如 eth0, ens33)
if_up_cmd = '/usr/bin/sudo /sbin/ip addr add $_IP_$/24 dev eth0 label eth0:0'
if_down_cmd = '/usr/bin/sudo /sbin/ip addr del $_IP_$/24 dev eth0'
# 发送 ARP 广播
arping_cmd = '/usr/bin/sudo /usr/sbin/arping -U $_IP_$ -w 1 -I eth0'

# 监控对方节点
other_pgpool_hostname0 = '192.168.1.102'
other_pgpool_port0 = 9999
other_wd_port0 = 9000

# --- 节点 2 特有配置 (注意 wd_hostname) ---
# 在节点 2 上，wd_hostname = '192.168.1.102'
# 其他配置保持一致
```

#### 3. 配置 pcp.conf
用于 Pgpool 的管理命令认证。在两个节点上执行：
```bash
# 生成 admin 用户的 md5 密码
pg_md5 admin_password

# 编辑 /etc/pgpool-II/pcp.conf
admin:md5xxxxxxxxxx
```

#### 4. 配置 sudo 权限 (用于 VIP 漂移)
因为 Pgpool 通常以 `postgres` 或 `pgpool` 用户运行，但管理 IP 需要 root 权限。
在 **两个节点** 上执行 `visudo` 添加：
```text
postgres ALL=NOPASSWD: /sbin/ip
postgres ALL=NOPASSWD: /usr/sbin/arping
```

---

### 🚀 第三阶段：启动与验证

#### 1. 启动服务
在两个节点上依次启动 Pgpool-II：
```bash
# 先启动节点 1 (期望成为 Master)
systemctl start pgpool-II
# 再启动节点 2
systemctl start pgpool-II
```

#### 2. 验证状态
使用 `pcp` 命令或 SQL 查看状态。

**查看节点状态：**
```bash
# 在任意节点执行
psql -h 192.168.1.101 -p 9999 -U pgpool postgres -c "SHOW POOL_NODES;"
```
*预期结果：*
*   `node_id 0` (Primary) 状态应为 `up`。
*   `node_id 1` (Standby) 状态应为 `up`。
*   `replication_state` 应显示 `streaming`。

**验证 VIP 漂移：**
1.  检查 VIP 是否在节点 1 上：`ip addr show`。
2.  模拟故障：停止节点 1 的 Pgpool 服务 (`systemctl stop pgpool-II`)。
3.  检查 VIP 是否自动漂移到了节点 2。
4.  应用程序连接 `192.168.1.200:9999` 应依然正常。

### 💡 常见问题与建议

1.  **脑裂问题**：在双节点 Pgpool 中，如果心跳线断开，可能会发生脑裂。建议配置 `heartbeat` 模式（在 `pgpool.conf` 中配置 `heartbeat_destination`），而不是默认的 `query` 模式，这样更稳定。
2.  **在线恢复**：当旧的主库修好后，可以使用 Pgpool 的在线恢复功能将其重新加入集群，无需手动重做备库。这需要配置 `recovery_1st_stage` 脚本（参考 pgpool 官方文档或搜索结果中的脚本配置）。
3.  **应用连接**：应用程序的连接串应指向 **VIP** (`192.168.1.200`) 和 **Pgpool 端口** (`9999`)。

通过以上步骤，你就拥有了一个具备自动故障切换、读写分离能力的 PostgreSQL 高可用集群。
