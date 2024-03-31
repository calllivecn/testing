#!/bin/bash
# date 2022-04-15 12:08:42
# author calllivecn <calllivecn@outlook.com>

tmp=$(mktemp -u --suffix=rshell-XXXX)

exit_clear(){
	rm -v $tmp
}

mkfifo $tmp

bash -i < $tmp |& nc -l 18022 > $tmp
