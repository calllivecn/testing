#!/bin/bash
# date 2020-06-06 20:10:01
# author calllivecn <c-all@qq.com>



for c in {1..255}
do
	echo -en "\e[38;5;${c}m${c} "
done

