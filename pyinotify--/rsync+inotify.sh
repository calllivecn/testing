#!/bin/bash
# date 2023-06-13 18:35:05
# author calllivecn <c-all@qq.com>

SSH_HOST="tenw"

SRC_Path="/home/test"
DEST="$HOME/rsyncfile"

monitor(){
	inotifywait -mrq --format '%w%f' -e create,close_write,delete $1 | while read line; do
	    if [ -f $line ]; then
	        #rsync -avz --password-file=/etc/rsyncd.pass --delete "$line" "$SSH_HOST":${module}
	        rsync -avz --delete "$line" "$SSH_HOST":${DEST}
	    else
	        cd $1 && rsync -avz --delete "$line" "$SSH_HOST":${DEST}
	    fi
	done
}

monitor $Path

