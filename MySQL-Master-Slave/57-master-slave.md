
# 5.7 主从配置, 默认的异步复制模式。

## 需要在默认配置之上，添加配置

- 这是master

	```ini
	server-id=1
	gtid-mode=on
	enforce-gtid-consistency=on

	log-slave-updates=on
	log-bin=mysql-bin
	binlog_format=row
	expire_logs_days = 7

	# 启用半同步主从复制
	plugin-load="rpl_semi_sync_master=semisync_master.so;rpl_semi_sync_slave=semisync_slave.so"
	rpl_semi_sync_master_enabled=1

	```

- 这是slave

	```ini
	server-id=10
	gtid-mode=on
	enforce-gtid-consistency=on

	log-slave-updates=on
	log-bin=mysql-bin
	binlog_format=row
	expire_logs_days = 7

	# 启用半同步主从复制
	plugin-load="rpl_semi_sync_master=semisync_master.so;rpl_semi_sync_slave=semisync_slave.so"
	rpl_semi_sync_slave_enabled=1
	```

## 在容器中使用官方docker.io/library/mysql:5.7 做实验时，

- 首先从启动一个容器，从里拿到默认配置文件 podman cp \<container\_name\>:/etc/my.cnf 复制出来原本的配置

- 需要先从 podman cp \<container\_name\>:/etc/my.cnf 复制出来原本的配置

- 分别在my-m.cnf 中添加上面提到主从配置部分

- 分别在my-s.cnf 中添加上面提到主从配置部分

- 在启动新的容器，时映射配置。




# 5.7 在一个已有的异步同步方式的主从集群上， 启用半同步复制。


## 1. 在主库上执行

- 安装插件

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
	mysql> INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so';
	```

	- 记录下删除插件命令：uninstall plugin rpl_semi_sync_slave;

- 动态开启半同步功能(免重启立即生效)
	```shell
	mysql> SET GLOBAL rpl_semi_sync_master_enabled=1;
	```

- 需要写入配置文件重启后才会生效

	```ini
	[mysqld]
	# 启用半同步主从复制
	plugin-load="rpl_semi_sync_master=semisync_master.so;rpl_semi_sync_slave=semisync_slave.so"
	rpl_semi_sync_master_enabled=1

	# 添加或者修改，默认的超时是10s
	#rpl_semi_sync_master_timeout=3000
	```

## 2. 从节点配置

- 同样安装插件

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_master SONAME 'semisync_master.so';
	mysql> install plugin rpl_semi_sync_slave SONAME 'semisync_slave.so';
	```

- 动态开启半同步功能(免重启立即生效)

	```shell
	mysql> SET GLOBAL rpl_semi_sync_slave_enabled=1; #临时修改变量
	```

- 需要写入配置文件重启后才会生效

	```ini
	[mysqld]
	# 启用半同步主从复制
	plugin-load="rpl_semi_sync_master=semisync_master.so;rpl_semi_sync_slave=semisync_slave.so"
	rpl_semi_sync_slave_enabled=1

	# 添加或者修改，默认的超时是10s
	#rpl_semi_sync_slave_timeout=3000
	```

- **要先检测一个 slave 的半同步配置，然后在检测 master 的。**

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
