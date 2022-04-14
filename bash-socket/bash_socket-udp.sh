#!/bin/bash
# date 2022-03-16 13:16:34
# author calllivecn <c-all@qq.com>

set -e

clean(){
	if [ -e /proc/$$/fd/9 ];then
		#exec 9>&-
		#exec 9<&-
		:
	fi
	exit 1
}

trap clean EXIT ERR SIGINT

recv(){


	#exec 9<>/dev/udp/127.0.0.1/6789
	nc -u -l 6789 | while read data;
	do
		echo "接收数据：$data"
	done

}


send(){
	#echo -n "$2" >/dev/udp/$1/6789
	ack=$(echo "$1" |nc -u 127.0.0.1 6789)
	echo "$ack"
}

if [ "$1"x == "send"x ];then
	shift
	send $@
elif [ "$1"x == "recv"x ];then
	recv
else
	shift
	send $@
fi
