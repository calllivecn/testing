#!/bin/bash
# date 2023-03-27 22:58:39
# update 2025-11-17
# author calllivecn <calllivecn@outlook.com>

# 测试flock 的使用
#
# 并行A,B两条执行流(模拟线程)。
# A在执行前先检测B任务是否已经在执行：
#	B执行中：等B退出后在检测B是否执行成功。
#		成功：A就退出
#		失败：A开始执行
#	B未执行：
#		A执行
#
# B同A的执行, BA的角色互换。

tmp_unlock=$(mktemp)
tmp_unlock_ok="${tmp_unlock}-ok"

trap "rm $tmp_unlock $tmp_unlock_ok" EXIT

disk_unlock(){
	if [ -f "$tmp_unlock_ok" ];then
		return 0
	fi
	
	# A, B 两个操作
	if [ "$1"x = Ax ];then
		echo "A 的解锁过程..."
		# 执行耗时
		read -p "用户输入：" pw
		# 模拟执行成功，或者失败
		:>"$tmp_unlock_ok"
		echo "A 的解锁过程... done"
	else
		echo "B 的解锁过程..."
		# 执行耗时
		sleep 30
		:>"$tmp_unlock_ok"
		#echo "B 的解锁过程... failed"
		echo "B 的解锁过程... done"
	fi
}


A(){
	{
		echo "A pid: $$"
		flock -n 200
		echo "A 执行..."
		disk_unlock A
	} 200>"$tmp_unlock"
}

B(){
	(
		echo "B pid: $$"
		flock -n 200
		echo "B 执行..."
		disk_unlock B
	) 200>"$tmp_unlock"

}


A & 
pid_a=$1
B &
pid_b=$1

wait $pid_a $pid_b

