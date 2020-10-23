#!/bin/bash
# date 2020-10-23 11:11:57
# author calllivecn <c-all@qq.com>


process=4
url="http://172.17.0.1:6785/calllivecn"
url=

if [ -z "$1" ];then
	echo "请给出http地址."
	exit 1
else
	url="$1"
fi

if [ -z "$2" ];then
	process=4
else
	process="$2"
fi

pids=("index")
for i in $(seq $process)
do
	docker run -i --rm apache-ab ab -c 1000 -n 10000 ${url} > /tmp/ab-${i}.report 2>&1 &
	pids[$i]=$!
done

for i in $(seq $process)
do
	wait ${pids[$i]}
	echo "pid: ${pids[$i]} 完成"
done
