#!/bin/bash
# date 2021-01-04 11:29:34
# author calllivecn <c-all@qq.com>

param(){
	if [ "${2::1}" = "-" ] || [ "${2::2}" = "--" ];then
		echo "$1需要参数"
		exit 1
	fi
}

for args in $@
do
	case $args in
		-a|--aone)
			echo "A 能匹配到长选项吗？"
			shift
			param "$args" "$1"
			AONE="$1"
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
			echo "???"
			;;
	esac
	shift
done


echo "你输入的参数：$AONE"

echo $@
