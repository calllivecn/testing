#!/bin/bash


getch(){
    stty -icanon -echo
    dd if=$(tty) bs=8 count=1 2> /dev/null
    stty icanon echo
}


move(){
if [ "$1"x = "j"x -o "$1"x = "[B"x ];then
    echo -en "\033[B"
elif [ "$1"x = "k"x -o "$1"x = "[A"x ];then
    echo -en "\033[A"
elif [ "$1"x = "h"x -o "$1"x = "[D"x ];then
    echo -en "\033[D"
elif [ "$1"x = "l"x -o "$1"x = "[C"x ];then
    echo -en "\033[C"
else
    echo -n "h,j,k,l or q->quit"
fi
}

quit(){
stty icanon echo
exit 0
}

trap quit SIGINT

while :
do
    me=$(getch)
    if [ "$me"x = "q"x -o "$me"x = ""x ];then
        echo exit.
        break
    fi
    move $me
done
