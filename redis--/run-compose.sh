#!/bin/bash
# date 2024-02-04 08:07:07
# author calllivecn <c-all@qq.com>

# 在容器中时，还是指定下配置文件，在sentinel 和 cluster 模式中，都会自动写回配置的。

IP_PREFIX="172.20.1"

# 如果在创建容器时，不--ip指定ip。ip 会在多少启停的容器之间漂移。
docker network create redis --subnet "${IP_PREFIX}.0/24" --gateway "${IP_PREFIX}.200"

init(){
	for i in $(seq 1 6)
	do
		docker run -d --name "redis${i}" --network redis --ip "${IP_PREFIX}.${i}" rediszx:latest /data/redis-cluster.conf
	done
}


# 扩容的时候一般会一次添加1主1从
add_node_2(){
	for i in $(seq 7 8)
	do
		docker run -d --name "redis${i}" --network redis --ip "${IP_PREFIX}.${i}" rediszx:latest /data/redis-cluster.conf
	done
}

init

#add_node_2

