#!/bin/bash

machine="10.1.2.6:15555"
localipport="10.1.2.1:5901"
phone="10.1.2.100"

phonename="COL-AL10"

turn_off(){
	for i in $(seq 60)
	do
		#oppo_win=$(xdotool search --name PDVM00)
		oppo_win=$(xdotool search --name "$phonename")
		if [ "$oppo_win"x != x ];then
			xdotool key --window $oppo_win ctrl+o
			break
		else
			sleep 1
		fi

		if [ $i -gt 60 ];then
			break
		fi
	done
}

Connect(){

	turn_off &
	
	adb connect $machine
	# fps only support android 10
	#scrcpy -s $machine --bit-rate 1M --max-size 800 --max-fps 15
	scrcpy -s $machine --bit-rate 1M --max-size 800
}

CloseConnect(){
	while :;
	do
		if ss dst "$phone" |grep -q "$localipport";then
			:
		else
			oppo_win=$(xdotool search --name "$phonename")
			if [ "$oppo_win"x != x ];then
				xdotool key --window $oppo_win alt+F4
			else
				break
			fi
		fi
		sleep 2
	done
}

# 长时间不连接，wg 可能会断开。
SleepAutoConnect(){
	Connect
}

# 检测phone 是否连接
test_phone(){
	while :;
	do
		if ss dst "$phone" |grep -q "$localipport";then
			CloseConnect &
			Connect
		else
			sleep 2
		fi
	done
}

test_phone
