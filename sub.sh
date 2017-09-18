#!/bin/bash


date +%F-%R

count=0
while :
do
	echo -n "my cmd > "
	read line
	if [ "$line"x = "exit"x ];then
		break
	elif [ "$line"x = ""x ];then
		continue
	fi
	
	if [ $count -eq 3 ];then
		date +%s
	fi
	count=$[count+1]
	echo "$line"
done


