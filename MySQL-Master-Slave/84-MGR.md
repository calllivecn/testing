
# 8.4 MGR 组复制

## 需要在默认配置之上，添加配置

- 这是 MGR1

	```ini
	[mysqld]

	#
	# Disable other storage engines
	#
	disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"

	#
	# Replication configuration parameters
	#
	server-id=1
	gtid_mode=ON
	enforce_gtid_consistency=ON
	#binlog_checksum=NONE           # Not needed in 8.0.21 or later

	#
	# Group Replication configuration
	#
	plugin_load_add='group_replication.so'
	group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
	group_replication_start_on_boot=off
	group_replication_local_address="s2:33061"
	group_replication_group_seeds="s1:33061,s2:33061,s3:33061"
	group_replication_bootstrap_group=off
	```

	- group_replication_group_name的值必须是有效的 UUID。您可以使用SELECT UUID()来生成一个。此 UUID 构成 GTID 的一部分，当组成员从客户端接收事务以及组成员内部生成的视图更改事件写入二进制日志时，将使用 GTID。
	- 配置 group_replication_start_on_boot 变量off指示插件在服务器启动时不自动启动操作。这在设置组复制时很重要，因为它确保您可以在手动启动插件之前配置服务器。配置成员后，您可以设置 group_replication_start_on_boot on以便组复制在服务器启动时自动启动。
	- 配置 group_replication_local_address 设置成员用于与组中其他成员进行内部通信的网络地址和端口。组复制使用此地址进行涉及组通信引擎（XCom，Paxos 变体）远程实例的内部成员到成员连接。



## 在容器中使用官方docker.io/library/mysql:8.4 时，

- 需要先从 podman cp \<container\_name\>:/etc/my.cnf 复制出来原本的配置

- 分别在my-mgr.cnf 中添加上面提到主从配置部分

- 在启动新的容器，时映射配置。


## 20.2.1.3 分布式恢复的用户凭证；要创建分布式恢复的复制用户，请执行以下步骤：

- 创建组复制用户+给权限

	```sql
	mysql> CREATE USER mgr_user@'%' IDENTIFIED BY 'password';
	mysql> GRANT REPLICATION SLAVE ON *.* TO mgr_user@'%';
	mysql> GRANT CONNECTION_ADMIN ON *.* TO mgr_user@'%';
	mysql> GRANT BACKUP_ADMIN ON *.* TO mgr_user@'%';
	mysql> GRANT GROUP_REPLICATION_STREAM ON *.* TO mgr_user@'%';
	mysql> FLUSH PRIVILEGES;
	```

- 或者在 MySQL 8.0.23 或更高版本中：

	```sql
	mysql> CHANGE REPLICATION SOURCE TO SOURCE_USER='mgr_user', SOURCE_PASSWORD='password' FOR CHANNEL 'group_replication_recovery';
	```



## 首先需要确保服务器 s1 上安装了组复制插件。如果你用过 plugin_load_add='group_replication.so' 在选项文件中，则组复制插件已安装，您可以继续下一步。否则，必须手动安装插件；为此，请使用mysql客户端连接到服务器，并发出如下所示的 SQL 语句：

- 安装插件

	```shell
	mysql> INSTALL PLUGIN group_replication SONAME 'group_replication.so';

	mysql> SHOW PLUGINS;
	+----------------------------+----------+--------------------+----------------------+-------------+
	| Name                       | Status   | Type               | Library              | License     |
	+----------------------------+----------+--------------------+----------------------+-------------+
	| binlog                     | ACTIVE   | STORAGE ENGINE     | NULL                 | PROPRIETARY |

	(...)

	| group_replication          | ACTIVE   | GROUP REPLICATION  | group_replication.so | PROPRIETARY |
	+----------------------------+----------+--------------------+----------------------+-------------+
	```


## 20.2.1.5 引导组

- 第一次启动一个组的过程称为引导。您使用 group_replication_bootstrap_group 用于引导组的系统变量。引导程序只能由一台服务器完成，即启动该组的服务器，并且只能执行一次。这就是为什么它的价值 group_replication_bootstrap_group 选项未存储在实例的选项文件中。如果将其保存在选项文件中，则在重新启动时，服务器会自动引导具有相同名称的第二个组。这将导致两个不同的组具有相同的名称。同样的推理也适用于将此选项设置为ON情况下停止和重新启动插件。因此，要安全地引导该组，请连接到 s1 并发出以下语句：

	```sql
	mysql> SET GLOBAL group_replication_bootstrap_group=ON;
	mysql> START GROUP_REPLICATION;
	mysql> SET GLOBAL group_replication_bootstrap_group=OFF;
	```

- *或者，如果您正在为分布式恢复提供用户凭据 START GROUP_REPLICATION 语句（MySQL 8.0.21 及更高版本），发出以下语句：*

	```sql
	mysql> SET GLOBAL group_replication_bootstrap_group=ON;
	mysql> START GROUP_REPLICATION USER='mgr_user', PASSWORD='password';
	mysql> SET GLOBAL group_replication_bootstrap_group=OFF;
	```


- 一旦START GROUP_REPLICATION语句返回，该组就已启动。您可以检查该组现已创建并且其中有一名成员：


	```sql
	mysql> SELECT * FROM performance_schema.replication_group_members;
	+---------------------------+--------------------------------------+-------------+-------------+---------------+-------------+----------------+----------------------------+
	| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE  | MEMBER_ROLE | MEMBER_VERSION | MEMBER_COMMUNICATION_STACK |
	+---------------------------+--------------------------------------+-------------+-------------+---------------+-------------+----------------+----------------------------+
	| group_replication_applier | ce9be252-2b71-11e6-b8f4-00212844f856 |   s1        |       3306  | ONLINE        |             |                | XCom                       |
	+---------------------------+--------------------------------------+-------------+-------------+---------------+-------------+----------------+----------------------------+
	1 row in set (0.0108 sec)
	```


	- 此表中的信息确认组中存在具有唯一标识符的成员 ce9be252-2b71-11e6-b8f4-00212844f856 ，它处于ONLINE ，并且在s1上侦听端口3306上的客户端连接。


- 为了证明服务器确实在一个组中并且能够处理负载，创建一个表并向其中添加一些内容。

	```sql
	mysql> CREATE DATABASE test;
	mysql> USE test;
	mysql> CREATE TABLE t1 (c1 INT PRIMARY KEY, c2 TEXT NOT NULL);
	mysql> INSERT INTO t1 VALUES (1, 'Luis');
	```



## 20.2.1.6 将实例添加到组中

- 此时，该组中有一个成员，即服务器 s1，其中有一些数据。现在是时候通过添加之前配置的其他两台服务器来扩展该组了。
- 添加第二个实例


- 为了添加第二个实例（服务器 s2），首先为其创建配置文件。除了server_id等内容之外，该配置与服务器 s1 所使用的配置类似。


	```ini
	[mysqld]

	#
	# Disable other storage engines
	#
	disabled_storage_engines="MyISAM,BLACKHOLE,FEDERATED,ARCHIVE,MEMORY"

	#
	# Replication configuration parameters
	#
	server_id=2
	gtid_mode=ON
	enforce_gtid_consistency=ON
	#binlog_checksum=NONE           # Not needed in 8.0.21 or later

	#
	# Group Replication configuration
	#
	plugin_load_add='group_replication.so'
	group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
	group_replication_start_on_boot=off
	group_replication_local_address="s2:33061"
	group_replication_group_seeds="s1:33061,s2:33061,s3:33061"
	group_replication_bootstrap_group=off
	```

- 与服务器 s1 的过程类似，使用就位的选项文件启动服务器。

	```sql
	SET SQL_LOG_BIN=0;
	CREATE USER mgr_user@'%' IDENTIFIED BY 'password';
	GRANT REPLICATION SLAVE ON *.* TO mgr_user@'%';
	GRANT CONNECTION_ADMIN ON *.* TO mgr_user@'%';
	GRANT BACKUP_ADMIN ON *.* TO mgr_user@'%';
	GRANT GROUP_REPLICATION_STREAM ON *.* TO mgr_user@'%';
	FLUSH PRIVILEGES;
	SET SQL_LOG_BIN=1;
	```

	- 如果您使用CHANGE REPLICATION SOURCE TO提供用户凭据，请在此之后发出以下语句：
  
	```sql
	CHANGE REPLICATION SOURCE TO SOURCE_USER='mgr_user', SOURCE_PASSWORD='password' \
	FOR CHANNEL 'group_replication_recovery';
	```

	- *如有必要，请安装组复制插件*

	- 启动组复制，s2 开始加入组的过程。


	```sql
	mysql> START GROUP_REPLICATION;

	# 如果您要为分布式恢复提供用户凭据作为 START GROUP_REPLICATION ，你可以这样做：
	mysql> START GROUP_REPLICATION USER='mgr_user', PASSWORD='password';
	```


	- 与前面在 s1 上执行的步骤相同的步骤不同，这里的不同之处在于您不需要引导该组，因为该组已经存在。换句话说，在 s2 上 group_replication_bootstrap_group 设置为OFF ，并且您不发出 SET GLOBAL group_replication_bootstrap_group=ON; 在开始组复制之前，因为该组已由服务器 s1 创建并引导。此时只需要将服务器s2添加到已经存在的组中即可。


- 检查 performance_schema.replication_group_members 表再次显示该组中现在有两个ONLINE服务器。

	```sql
	mysql> SELECT * FROM performance_schema.replication_group_members;
	+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+----------------------------+
	| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION | MEMBER_COMMUNICATION_STACK |
	+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+----------------------------+
	| group_replication_applier | 395409e1-6dfa-11e6-970b-00212844f856 |   s1        |        3306 | ONLINE       | PRIMARY     | 8.4.2          | XCom                       |
	| group_replication_applier | ac39f1e6-6dfa-11e6-a69d-00212844f856 |   s2        |        3306 | ONLINE       | SECONDARY   | 8.4.2          | XCom                       |
	+---------------------------+--------------------------------------+-------------+-------------+--------------+-------------+----------------+----------------------------+
	```



## 20.2.1.6.2 添加附加实例

- 向组中添加其他实例本质上与添加第二台服务器的步骤顺序相同，只是必须更改配置（因为服务器 s2 必须如此）。总结一下所需的操作：
  
  1. 创建配置文件
  2. 启动服务器并连接到它。创建用于分布式恢复的复制用户。
  3. 如有必要，安装组复制插件
  4. 启动组复制


