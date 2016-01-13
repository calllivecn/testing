#!/usr/bin/env python3
#coding=utf-8

import sys,os

file_size = os.stat(sys.argv[1]).st_size



f = open(sys.argv[1],'r+')

l=['0'*4096]

while file_size > 0:
		if file_size > 4096:
				f.writelines(l)
				file_size -= 4096
		else:
				f.writelines(['0'*file_size])
				file_size -= file_size
		f.flush()



f.close()


os.remove(sys.argv[1])


