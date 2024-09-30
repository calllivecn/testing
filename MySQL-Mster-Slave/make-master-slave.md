
# 当前是8.0 主从配置

## 需要在默认配置之上，添加配置

- 这是master

	```ini
	server-id=1
	gtid-mode=on
	enforce-gtid-consistency=on
	log-slave-updates=on
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



