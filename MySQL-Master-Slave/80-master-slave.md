
# 8.0 主从配置, 默认的异步复制模式。(实验验证ok)

## 需要在默认配置之上，添加配置

- 这是source

	```ini
	server-id=1
	gtid-mode=on
	enforce-gtid-consistency=on
	log_replica_updates=on

	# 8.0 需要在 mysql initialization 之后 在写入配置, 不能直接修改配置后做为首次启动。

	# 在半同步配置完成后，把默认启用写入配置文件 
	rpl_semi_sync_source_enabled=1

	```

- 这是replica

	```ini
	server-id=10
	gtid-mode=on
	enforce-gtid-consistency=on

	# 8.0 需要在 mysql initialization 之后 在写入配置, 不能直接修改配置后做为首次启动。
	# 8.0.26 之后
	~~plugin-load-add="rpl_semi_sync_source=semisync_source.so"~~
	~~plugin-load-add="rpl_semi_sync_replica=semisync_replica.so"~~

	# 在半同步配置完成后，把默认启用写入配置文件 
	rpl_semi_sync_replica_enabled=1

	```

## 在容器中使用官方docker.io/library/mysql:8.0 时，

- 需要先从 podman cp \<container\_name\>:/etc/my.cnf 复制出来原本的配置

- 分别在my-m.cnf 中添加上面提到主从配置部分

- 分别在my-s.cnf 中添加上面提到主从配置部分

- 在启动新的容器，时映射配置。


# 8.0 在已经存在的主从中， 加上半同步复制。

## 1. 在主库上执行

- 安装插件

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_master soname 'semisync_master.so'; #永久安装插件

	#Or from MySQL 8.0.26:
	mysql> install plugin rpl_semi_sync_replica soname 'semisync_replica.so'; #永久安装插件
	```

- 临时开启半同步功能(免重启立即生效)

	```shell
	mysql> SET GLOBAL rpl_semi_sync_master_enabled=1;

	#Or from MySQL 8.0.26:
	mysql> SET GLOBAL rpl_semi_sync_source=1;
	```


- 需要在安装插件, 并启用半同步成功后才能将以下配置**写入配置文件**

	```ini
	[mysqld]

	# 8.0.26 之后, 
	#这不行，不能在初始化时添加插件
	~~plugin-load-add="rpl_semi_sync_source=semisync_source.so"~~
	~~plugin-load-add="rpl_semi_sync_replica=semisync_replica.so"~~

	# 在半同步配置完成后，把默认启用写入配置文件 
	#Or from MySQL 8.0.26 with the rpl_semi_sync_source plugin:
	rpl_semi_sync_source_enabled=1

	# 添加或者修改，默认的超时是10s
	rpl_semi_sync_source_timeout=3000
	```

## 2. 从节点配置

- 同样安装插件 **(注意名称不一样)**

	```shell
	mysql> INSTALL PLUGIN rpl_semi_sync_slave SONAME 'semisync_slave.so'; #永久安装插件
	```

- 临时开启半同步功能(免重启立即生效)

	```shell
	mysql> SET GLOBAL rpl_semi_sync_slave_enabled=1; #临时修改变量
	# 8.0.26 之后 ？
	mysql> SET GLOBAL rpl_semi_sync_replica=1; #临时修改变量
	```

- 需要在安装插件后才能配置;从节点修改配置文件并设定半同步阈值 **(根据你的场景，判断是否需要写入配置文件)**

	```ini
	[mysqld]

	# 在半同步配置完成后，把默认启用写入配置文件 
	rpl_semi_sync_replica_enabled=1

	# 添加或者修改，默认的超时是10s
	rpl_semi_sync_replica_timeout=3000
	```

- **要先检测第一个 replica 的 半同步配置，然后在检测 source 的。**

- 从节点确认配置生效 **注意:如果已经实现主从复制,需要stop replica;start replica;**

	```shell
	mysql> stop replica;start replica;
	Query OK, 0 rows affected, 1 warning (0.00 sec)
	Query OK, 0 rows affected, 1 warning (0.01 sec)


	mysql> show global variables like "%semi%";
	+---------------------------------+-------+
	| Variable_name                   | Value |
	+---------------------------------+-------+
	| rpl_semi_sync_replica_enabled     | ON    |
	| rpl_semi_sync_replica_trace_level | 32    |
	+---------------------------------+-------+

	mysql> show global status like "%semi%";
	+----------------------------+-------+
	| Variable_name              | Value |
	+----------------------------+-------+
	| Rpl_semi_sync_replica_status | ON    |
	+----------------------------+-------+
	1 row in set
	Time: 0.027s
	```

- 主节点确认配置生效

	- 主要查看: `rpl_semi_sync_source_enabled=ON`
	- 和: `Rpl_semi_sync_source_status=ON` 和 `Rpl_semi_sync_source_clients >= 1`

	```shell
	mysql> show global variables like '%semi%';
	+-------------------------------------------+------------+
	| Variable_name                             | Value      |
	+-------------------------------------------+------------+
	| rpl_semi_sync_source_enabled              | ON         |
	| rpl_semi_sync_source_timeout              | 10000      |
	| rpl_semi_sync_source_trace_level          | 32         |
	| rpl_semi_sync_source_wait_for_slave_count | 1          |
	| rpl_semi_sync_source_wait_no_slave        | ON         |
	| rpl_semi_sync_source_wait_point           | AFTER_SYNC |
	+-------------------------------------------+------------+
	6 rows in set
	Time: 0.028s
	
	mysql> show global status like "%semi%";
	+--------------------------------------------+-------+
	| Variable_name                              | Value |
	+--------------------------------------------+-------+
	| Rpl_semi_sync_source_clients               | 1     |
	| Rpl_semi_sync_source_net_avg_wait_time     | 0     |
	| Rpl_semi_sync_source_net_wait_time         | 0     |
	| Rpl_semi_sync_source_net_waits             | 0     |
	| Rpl_semi_sync_source_no_times              | 0     |
	| Rpl_semi_sync_source_no_tx                 | 0     |
	| Rpl_semi_sync_source_status                | ON    |
	| Rpl_semi_sync_source_timefunc_failures     | 0     |
	| Rpl_semi_sync_source_tx_avg_wait_time      | 0     |
	| Rpl_semi_sync_source_tx_wait_time          | 0     |
	| Rpl_semi_sync_source_tx_waits              | 0     |
	| Rpl_semi_sync_source_wait_pos_backtraverse | 0     |
	| Rpl_semi_sync_source_wait_sessions         | 0     |
	| Rpl_semi_sync_source_yes_tx                | 0     |
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

```shell
Last_IO_Errno                 | 2061
Last_IO_Error                 | Error connecting to source 'replica@mysql80-master:3306'. This was attempt 3/86400, with a delay of 60 seconds between attempts. Message: Authentication plugin 'caching_sha2_password' reported error: Authentication requires secure connection.
```


## 8.0 初始化时 不能加载 插件 的问题

```shell
[Warning] [MY-013501] [Server] Ignoring --plugin-load[_add] list as the server is running with --initialize(-insecure).
```

- 解决：在实例 initialize 之后，在添加 plugin-load-add=