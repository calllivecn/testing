#!/bin/bash
# date 2018-12-07 15:39:07
# author calllivecn <c-all@qq.com>

set -e

logs(){

echo "$1"
echo "$1" >> "$0".logs

}

pwddir=$(pwd)

tmpfile=$(mktemp -p "${pwddir}")

safe_exit(){

	rm "${tmpfile}" ${tmpfile}-* "$0".logs
}

trap safe_exit ERR 

dd_test(){

	dd if=/dev/urandom bs=1M count=500 | base64 > "${tmpfile}"
}

dd_test


for compress in pigz pbzip2 pxz;
do
	for level in $(seq 1 9)
	do
		
		outfile="${tmpfile}-level${level}.${compress}"

		logs "$compress -k -c -${level} "${tmpfile}" > ${outfile}"

		start_=$(date +%s)

		$compress -k -c -${level} "${tmpfile}" > "${outfile}"

		end=$(date +%s)

		logs "压缩耗时：$[ end - start_]"


		start_=$(date +%s)
		
		$compress -k -dc "${outfile}" > /dev/null
		
		end=$(date +%s)
		
		logs "解压耗时：$[end - start_]"
	done
done

