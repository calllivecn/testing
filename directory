#!/usr/bin/env python3
#coding=utf-8

import os,sys



PATH=sys.argv[1]

PATH = os.path.abspath(PATH)

def pathFile(PATH):
	for root,dirs,files in os.walk(PATH):
		for f in files:
			#root=root.lstrip(PATH)
			print(os.path.join(root,f),flush=True)
			#print(root,dirs,files)
			#input()


def p2(PATH):
	for r,d,f in os.walk(PATH):
		for fs in f:
			print(os.path.abspath(fs))
			
			
pathFile(PATH)



