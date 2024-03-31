#!/usr/bin/env python3
#coding=utf-8
# date 2018-01-05 05:56:32
# author calllivecn <calllivecn@outlook.com>

import os
from multiprocessing import Process,cpu_count

def run():
    try:
	    a=0
	    while True:
	    	a+=1
	    	if a >= 10000:
	    		a=0
    except KeyboardInterrupt:
        pass


proc_list=[]
for i in range(cpu_count()):
	print('cpu:',i)
	proc = Process(target=run)
	proc.start()
	proc_list.append(proc)

try:
    for i in proc_list:
	    i.join()
except KeyboardInterrupt:
    print('exit')
