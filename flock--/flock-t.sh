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


A(){

	echo "执行 A pid: $$"
	while :;
	do
		{
			flock 20

			#disk_unlock A
			if [ -f "$tmp_unlock_ok" ];then
				echo "A 检测到已经解锁成功，退出当前操作。"
				return 0
			fi

			echo "A 的解锁过程..."
			# udevadm wait -t 10 "/dev/disk/by-uuid/XXXX-XXXX"
			# systemd-cryptsetup attach test-luks /dev/sdaX pw-file
			if sleep 5;then
				:>"$tmp_unlock_ok"
				echo "A 的解锁过程... done"
				return 0
			else
				echo "解锁失败，请重试："
			fi
			# 模拟执行成功，或者失败
			#:>"$tmp_unlock_ok"

		} 20>"$tmp_unlock"
	
	done
	echo "A 的解锁过程... done"
}

B(){
	echo "执行 B pid: $$"
	while :;
	do
		{
			flock 20

			# 每次等待用户输入密码时，检测是否已经解锁成功
			if [ -f "$tmp_unlock_ok" ];then
				echo "B 检测到已经解锁成功，退出当前操作。"
				return 0
			fi

			echo "B 的解锁过程..."
			echo -n "请输入解锁密码："
			read -t 3 pw

			if [ -n "$pw" ];then
				# systemd-cryptsetup attach test-luks /dev/sdaX pw-file
				if sleep 1 ;then
					:>"$tmp_unlock_ok"
					echo "B 的解锁过程... done"
					return 0
				else
					echo "解锁失败，请重试："
				fi
			fi

		} 20>"$tmp_unlock"
	done
}


A & 
pid_a=$1

sleep 1

B

wait $pid_a

