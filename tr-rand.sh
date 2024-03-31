#!/bin/bash
# date 2020-06-02 18:01:02
# author calllivecn <calllivecn@outlook.com>

# 拿到指定长度的随机可以字母和数字

if [ -n "$1" ];then
	tr -dc 'a-zA-Z0-9' < /dev/urandom |head -c "$1"
	echo
else
	tr -dc 'a-zA-Z0-9' < /dev/urandom |head -c 8
	echo
fi
