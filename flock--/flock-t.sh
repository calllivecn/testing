#!/bin/bash
# date 2023-03-27 22:58:39
# author calllivecn <calllivecn@outlook.com>

# 测试flock 的使用

tmp="/tmp/input"


t1(){
	echo "my pid: $$"
	echo "get lock..."
	flock -w 10 "$tmp" bash subproc.sh "$tmp" || echo "获取锁超时..."
	echo "done lock..."
}


t1 & 
t1 &

wait
