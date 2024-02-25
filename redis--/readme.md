# 测试 redis 运维过程

- pip install redis (py库)
- pip install iredis (命令行管理工具)
- pip install[hiredis] (为了获得更快的性能，请安装具有hiredis 支持的Redis。)

- docker pull redis:latest (使用的是官方提供的镜像v7.2.4 2024-02-07)

##  遇到的问题(已解决)

- ~~不管怎么使用集群写入过程，只要kill 掉其中一个 master ，在写入的客户端就会卡住（约120秒)。~~
- ~~就算已经有slave 节点顶上去了, 还是会 hug 住。~~
  >这个是socket_timeout参数调整的。
- ~~然后把刚刚kill 掉的 旧master 启动，它会自动恢复到集群里，但是现在它是slave角色。(这里可以连接到这台slave 执行 cluster failover，在把它切换成为master。)~~


- 在使用 redis-cli -c 连续写入时也出现上面的现象。

```shell
for i in $(seq 100000);do echo "setex number-${i} ${RANDOM}";do |redis-cli -c -h <ip:port>
```


# 创建集群

## 创建群集的指令

```shell
redis-cli -h ip
```
