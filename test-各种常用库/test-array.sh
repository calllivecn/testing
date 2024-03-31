#!/bin/bash
# date 2018-08-29 15:41:03
# author calllivecn <calllivecn@outlook.com>



array1=(a b c d e f)

if [ -n $array1 ];then
	echo 有
else
	echo 没有
fi


execoute_count=1
array_len=${#array1[@]}

for i in $( seq 0 $[array_len - 1 ] );
do
	execute_count=$[ execute_count + 1 ]
	echo -n "执行的第 $execute_count 次"
	echo "result: ${array1[${i}]}"
done
