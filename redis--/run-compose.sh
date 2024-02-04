#!/bin/bash
# date 2024-02-04 08:07:07
# author calllivecn <c-all@qq.com>

# 在容器中时，还是指定下配置文件，在sentinel 和 cluster 模式中，都会自动写回配置的。

init(){
	for i in $(seq 1 6)
	do
		docker create --name "redis${i}" --network redis redis:latest /etc/redis-cluster.conf
		docker cp cluster6379.conf "redis${i}:/etc/redis-cluster.conf"
		docker start "redis${i}"
	done
}


# 扩容的时候一般会一次添加1主1从
add_node_2(){
	for i in $(seq 7 8)
	do
		docker create --name "redis${i}" --network redis redis:latest /etc/redis-cluster.conf
		docker cp cluster6379.conf "redis${i}:/etc/redis-cluster.conf"
		docker start "redis${i}"
	done
}

add_node_2
