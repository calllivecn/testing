#!/bin/bash




while read -p "my cmd > " line
do
	if [ "$line"x = "exit"x ];then
		exit 0
	fi
	echo "$line"
done


