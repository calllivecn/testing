#!/usr/bin/bash



SELECT=(
" "
'select one'
'select two'
'select three'
'exit'
)

array_len=${#SELECT[@]}

ps3=$PS3

PS3='input number : '

select var in "${SELECT[@]:1:${array_len}}"
do
#PS3=$ps3
	case "$var" in
		${SELECT[1]})
			echo your ${SELECT[1]}
			;;
		${SELECT[2]})
			echo your ${SELECT[2]}
			;;
		${SELECT[3]})
			echo your ${SELECT[3]}
			;;
		${SELECT[4]})
			echo exit
			break
			;;
	esac

done
