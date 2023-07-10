#!/bin/bash
# date 2022-11-03 06:05:33
# author calllivecn <c-all@qq.com>

# "$1": 有off, on

. env.sh
if [ "$1"x = x ];then
	miiocli chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN info
else
	miiocli chuangmiplug --ip $MIROBO_IP --token $MIROBO_TOKEN "$1"
fi
