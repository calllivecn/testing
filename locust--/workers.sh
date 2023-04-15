#!/usr/bin/bash

CPU=$(nproc)


if [ -n "$2" ];then
	CPU="$2"
fi

procs=()

safe_exit(){
	local i
	for p in $(seq $CPU)
	do
		kill ${procs[p]}
	done
	echo "safe exit."
}

trap safe_exit SIGTERM EXIT ERR

for i in $(seq $CPU)
do
	locust --worker -f "$1"  &
	pid=$!
	procs[$i]=$pid
done

wait
