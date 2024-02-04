# redis cluter create 

## 创建3主集群 启动好至少3个容器后。之后可以动态向集群添加从节点

```shell
docker exec -it <container name> redis-cli --cluster create ip1:port1 ip2:port2 ip3:port3
```

## 创建3主3从集群 启动好至少6个容器后，

- --cluster-replicas 1，指定集群中的每个主节点有多少个从节点。

```shell
docker exec -it <container name> redis-cli --cluster create --cluster-replicas 1 ip1:port1 ip2:port2 ip3:port3 ip4:port4 ip5:port5 ip6:port6
```

