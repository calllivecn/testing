#!/bin/bash
# date 2018-12-07 15:39:07
# author calllivecn <c-all@qq.com>


logs(){

echo "$1"
echo "$1" >> "$0".logs

}


for compress in pigz pbzip2 pxz;
do
	for level in $(seq 1 9)
	do
		
		outfile="500M.test-level${level}.${compress}"

		logs "$compress -k -c -${level} 500M.test > ${outfile}"

		start_=$(date +%s)

		$compress -k -c -${level} 500M.test > "${outfile}"

		end=$(date +%s)

		logs "压缩耗时：$[ end - start_]"


		start_=$(date +%s)
		
		$compress -k -dc "${outfile}" > /dev/null
		
		end=$(date +%s)
		
		logs "解压耗时：$[end - start_]"
	done
done

