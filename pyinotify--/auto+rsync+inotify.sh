#!/bin/bash
# date 2023-06-13 18:35:05
# author calllivecn <calllivecn@outlook.com>

# 一次失败的尝试，没有达到想要的效果。
# 就是，自动实现同步本地和远程的两个目录，的增，删，改，创建。


# 这种方式，怎么感觉像是会丢掉事件一样？？？？
# 只要一次删除太多文件 rm -r zx* 这种，就会只检测到第一次的删除。
# 可是直接使用 inotifywait 命令时，又能检测到。。。。

SSH_HOST="routew"

SRC="/home/zx/test-rsyncfile"
DEST="/home/zx/data/test-rsyncfile"


monitor(){
	inotifywait -mrq --format '%e|%w%f' -e isdir,close_write,delete $1 | while read line;
	do
		a=($(echo "$line" |tr '|' ' '))

		event=${a[0]}
		filename=${a[1]}

		real_dest="${DEST}/${filename#${SRC}/}"

		echo "real dest path: $real_dest"

		# sleep 0.2
		# continue

		# 是目录
		if [[ "$event" = *ISDIR* ]];then
			
			# 是否是创建目录
			if [[ "$event" = *CREATE* ]];then
				ssh "$SSH_HOST" "mkdir -v ${real_dest}"
				
			elif [[ "$event" = *DELETE* ]];then
				ssh "$SSH_HOST" "rmdir -v ${real_dest}"
			fi

		# 是文件
		else

			# 是否是创建文件
			if [[ "$event" = *CLOSE_WRITE* ]];then
				scp "$filename" "$SSH_HOST:${real_dest}"
				
			elif [[ "$event" = *DELETE* ]];then
				ssh "$SSH_HOST" "rm -v ${real_dest}"

			fi

		fi

	done
}

#monitor $SRC


# 在删除或者创建目录都会触发
isdir_change(){
	inotifywait -qmr --format '%w%f' -e delete,isdir "$1" | while read line;
	do
		if [ -d "$line" ];then
			ssh "$SSH_HOST" "cd ${DEST};mkdir -v ${line}"
		else
			ssh "$SSH_HOST" "cd ${DEST};rmdir -v ${line}"
		fi
	done
}


# 文件写入完成(修改文件内容也会触发)
close_write(){
	inotifywait -qmr --format '%w%f' -e close_write "$1" | while read line;
	do
		scp "$line" "$SSH_HOST:${DEST}/"
	done
}


# 文件删除
delete_file(){
	inotifywait -qmr --format '%w%f' -e delete "$1" | while read line;
	do
		if [ -f "$line" ];then
			ssh "$SSH_HOST" "cd ${DEST};rm -v ${line}"
		fi
	done
}



PIDS=()
count=0

safe_exit(){
	for pid in ${PIDS[@]}
	do
		echo "kill $pid"
		kill $pid
	done
}

trap safe_exit ERR SIGTERM SIGINT

main(){
	#isdir_change "." &
	#pid=$!
	#PIDS[$count]=$pid

	#close_write "." &
	#pid=$!
	#PIDS[$count]=$pid

	#delete_file "." &
	#pid=$!
	#PIDS[$count]=$pid

	#wait

	monitor "$SRC"
}

main

