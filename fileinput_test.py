#!/usr/bin/env python3
#coding=utf-8


import fileinput


with fileinput.input() as f:
	for data in f:
		print(f.lineno(),data,end='')

		

