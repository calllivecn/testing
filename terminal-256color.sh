#!/bin/bash
# date 2020-06-06 20:10:01
# author calllivecn <calllivecn@outlook.com>


i=0
for c in $(seq 1 255)
do
	if [ $i -lt 10 ];then
		i=$[i+1]
	else
		echo
		i=0
	fi


	echo -en "\e[38;5;${c}m${c} "
done
echo
