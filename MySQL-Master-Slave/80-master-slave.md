
# 8.0 主从配置, 默认的异步复制模式。(实验验证ok)

## 需要在默认配置之上，添加配置

- 这是master

	```ini
	server-id=1
	gtid-mode=on
	enforce-gtid-consistency=on
	# 8.0 之前
	log-slave-updates=on
	# 8.0 开始
	log_replica_updates=on

	```

- 这是slave

	```ini
	server-id=10
	gtid-mode=on
	enforce-gtid-consistency=on

	```

## 在容器中使用官方docker.io/library/mysql:8.0 时，

- 需要先从 podman cp \<container\_name\>:/etc/my.cnf 复制出来原本的配置

- 分别在my-m.cnf 中添加上面提到主从配置部分

- 分别在my-s.cnf 中添加上面提到主从配置部分

- 在启动新的容器，时映射配置。


# 8.0 主从配置， 加上半同步复制。

## 0. 在前面默认主从的异步复制状态下，继续配置为半同步复制。

## 1. 在主库上执行

- 安装插件

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so'; #永久安装插件
	```

- 临时开启半同步功能(免重启立即生效)

	```shell
	# 8.0 之前
	mysql> SET GLOBAL rpl_semi_sync_master_enabled=1; #临时修改变量
	# 8.0 之后
	mysql> SET GLOBAL rpl_semi_sync_source=1; #临时修改变量
	```

- 需要在安装插件后才能配置;主节点修改配置文件并设定半同步阈值 **(根据你的场景，判断是否需要写入配置文件)**

	```ini
	[mysqld]

	# 添加或者修改 根据需要是否写入配置文件
	# 8.0 之前
	rpl_semi_sync_master_enabled=ON
	# 8.0 之后
	rpl_semi_sync_source=ON


	# 添加或者修改，默认的超时是10s
	rpl_semi_sync_master_timeout=3000
	```

## 2. 从节点配置

- 同样安装插件 **(注意名称不一样)**

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so'; #永久安装插件
	```

- 临时开启半同步功能(免重启立即生效)

	```shell
	mysql> SET GLOBAL rpl_semi_sync_slave_enabled=1; #临时修改变量
	# 8.0 之后 ？
	mysql> SET GLOBAL rpl_semi_sync_replica=1; #临时修改变量
	```

- 需要在安装插件后才能配置;从节点修改配置文件并设定半同步阈值 **(根据你的场景，判断是否需要写入配置文件)**

	```ini
	[mysqld]

	# 添加或者修改 根据需要是否写入配置文件
	rpl_semi_sync_slave_enabled=ON

	# 添加或者修改，默认的超时是10s
	rpl_semi_sync_slave_timeout=3000
	```

- **要先检测第一个 slave 的 半同步配置，然后在检测 master 的。**

- 从节点确认配置生效 **注意:如果已经实现主从复制,需要stop slave;start slave;**

	```shell
	mysql> stop slave;start slave;
	Query OK, 0 rows affected, 1 warning (0.00 sec)
	Query OK, 0 rows affected, 1 warning (0.01 sec)


	mysql> show global variables like "%semi%";
	+---------------------------------+-------+
	| Variable_name                   | Value |
	+---------------------------------+-------+
	| rpl_semi_sync_slave_enabled     | ON    |
	| rpl_semi_sync_slave_trace_level | 32    |
	+---------------------------------+-------+

	mysql> show global status like "%semi%";
	+----------------------------+-------+
	| Variable_name              | Value |
	+----------------------------+-------+
	| Rpl_semi_sync_slave_status | ON    |
	+----------------------------+-------+
	1 row in set
	Time: 0.027s
	```

- 主节点确认配置生效

	- 主要查看: `rpl_semi_sync_master_enabled=ON`
	- 和: `Rpl_semi_sync_master_status=ON` 和 `Rpl_semi_sync_master_clients >= 1`

	```shell
	mysql> show global variables like '%semi%';
	+-------------------------------------------+------------+
	| Variable_name                             | Value      |
	+-------------------------------------------+------------+
	| rpl_semi_sync_master_enabled              | ON         |
	| rpl_semi_sync_master_timeout              | 10000      |
	| rpl_semi_sync_master_trace_level          | 32         |
	| rpl_semi_sync_master_wait_for_slave_count | 1          |
	| rpl_semi_sync_master_wait_no_slave        | ON         |
	| rpl_semi_sync_master_wait_point           | AFTER_SYNC |
	+-------------------------------------------+------------+
	6 rows in set
	Time: 0.028s
	
	mysql> show global status like "%semi%";
	+--------------------------------------------+-------+
	| Variable_name                              | Value |
	+--------------------------------------------+-------+
	| Rpl_semi_sync_master_clients               | 1     |
	| Rpl_semi_sync_master_net_avg_wait_time     | 0     |
	| Rpl_semi_sync_master_net_wait_time         | 0     |
	| Rpl_semi_sync_master_net_waits             | 0     |
	| Rpl_semi_sync_master_no_times              | 0     |
	| Rpl_semi_sync_master_no_tx                 | 0     |
	| Rpl_semi_sync_master_status                | ON    |
	| Rpl_semi_sync_master_timefunc_failures     | 0     |
	| Rpl_semi_sync_master_tx_avg_wait_time      | 0     |
	| Rpl_semi_sync_master_tx_wait_time          | 0     |
	| Rpl_semi_sync_master_tx_waits              | 0     |
	| Rpl_semi_sync_master_wait_pos_backtraverse | 0     |
	| Rpl_semi_sync_master_wait_sessions         | 0     |
	| Rpl_semi_sync_master_yes_tx                | 0     |
	+--------------------------------------------+-------+
	14 rows in set
	Time: 0.020s
	```



## 3. 测试

```shell
# 在master实现，创建数据库，立即成功
MariaDB [db1]> create database db2;
Query OK, 1 row affected (0.004 sec)

# 在所有slave节点实现，停止复制线程
MariaDB [(none)]> stop slave;
Query OK, 0 rows affected (0.011 sec)

# 在master实现，创建数据库，等待3s才能成功
MariaDB [db1]> create database db3;
Query OK, 1 row affected (3.003 sec)

# 在任意一个slave节点实现，恢复复制线程
MariaDB [(none)]> start slave;
Query OK, 0 rows affected (0.006 sec)

# 在master实现，创建数据库，立即成功
MariaDB [db1]> create database db4;
Query OK, 1 row affected (0.002 sec)
```



# FQA

## 8.0 认证插件问题

```hell
Last_IO_Errno                 | 2061
Last_IO_Error                 | Error connecting to source 'replica@mysql80-master:3306'. This was attempt 3/86400, with a delay of 60 seconds between attempts. Message: Authentication plugin 'caching_sha2_password' reported error: Authentication requires secure connection.
```