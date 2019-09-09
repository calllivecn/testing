#!/bin/bash
# date 2019-04-28 09:44:21
# author calllivecn <c-all@qq.com>

set -e

exit_func(){
	echo "脚本退出，就会执行～～～"
}

trap exit_func EXIT


if [ -n "$1" ];then
	echo "成功~~~"
	exit 0
else
	echo "失败～～～"
	exit 1
fi

