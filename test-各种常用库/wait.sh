#!/bin/bash
# date 2018-08-29 11:10:18
# author calllivecn <c-all@qq.com>


sleep 500 &
pid1=$!
echo $pid1

sleep 500 &
pid2=$!
echo $pid2

echo "wait..."

wait %1 %2
