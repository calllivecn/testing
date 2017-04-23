#!/bin/bash


getch(){
	#stty cbreak -echo
	stty -icanon -echo
	dd if=$(tty) bs=1 count=1 2> /dev/null
	#stty -cbreak echo
	stty icanon echo
}


move(){
if [ "$1"x = "j"x ];then
	echo -en "\033[B"
elif [ "$1"x = "k"x ];then
	echo -en "\033[A"
elif [ "$1"x = "h"x ];then
	echo -en "\033[D"
elif [ "$1"x = "l"x ];then
	echo -en "\033[C"
else
	echo -n "h,j,k,l or q->quit"
fi
}

quit(){
:
}

trap -- quit SIGINT

while :
do
	me=$(getch)
	if [ "$me"x = "q"x ];then
		echo exit.
		break
	fi
	move $me
done
