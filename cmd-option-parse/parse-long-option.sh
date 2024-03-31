#!/bin/bash
# date 2021-01-04 11:29:34
# author calllivecn <calllivecn@outlook.com>

param(){
	if [ "${2::1}" = "-" ] || [ "${2::2}" = "--" ];then
		echo "$1需要参数"
		exit 1
	fi
}
ARGS_C=0
ARGS=()

#for args in $@ # 这种方式，shift后，第二次循环时，后面的参数还在.
while :
do
	echo "---------------------------------------------"
	echo "当前还有参数：$@"

	case "$1" in
		-a|--a-one)
			param "$args" "$2"
			AONE="$2"
			echo "A 能匹配到长选项吗？添加 $AONE"
			shift
			;;
		-b|--btwo)
			echo "B 能匹配到长选项吗？"
			;;
		-c|--bthree)
			echo "C 能匹配到长选项吗？"
			;;
		-h|--help)
			usage
			exit 0
			;;
		--)
			break
			echo "--"
			;;
		-a)
			echo "还能在匹配一次？？？"
			;;
		*)
			echo "$1 添加到位置参数"
			ARGS[$ARGS_C]="$1"
			ARGS_C=$[ARGS_C + 1]
			;;
	esac

	echo "execoute: shift"
	shift
	if [ $# -eq 0 ];then
		break
	fi
done
set -- ${ARGS[@]}
unset ARGS ARGS_C


echo "你输入的参数：$AONE"

echo "这里位置参数：$@"
