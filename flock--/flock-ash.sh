#!/bin/ash


lock="$(mktemp)"

A(){
	
	(
		exec 20>>"$lock"
		echo 'A exec 20 ok'
		flock 20

		echo "A 执行..."
		echo line1
		echo line2
		sleep 3
		echo line3

		exec 20>&-
	)
	
}

B(){
	
	(
		exec 20>>"$lock"
		echo 'B exec 20 ok'
		flock 20

		echo "B 执行..."
		echo line1
		echo line2
		echo line3
		echo "回车继续..."
		read -t 3 data

		exec 20>&-
	)
	
}


A &
pid_a=$!

B 

wait $pid_a

echo ok

