#!/bin/bash
# date 2018-01-18 00:06:06
# author calllivecn <calllivecn@outlook.com>

getch(){

local TTY 

TTY=$(tty)

stty -icanon -echo

dd if=$TTY bs=8 count=1 2> /dev/null

stty icanon echo

}



while :
do
	cmd=$(getch)
	if [ "$cmd"x = "q"x ];then
		exit 0
	fi
	aplay 打字机1_2声.wav
done



