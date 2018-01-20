#!/usr/bin/env python3
#coding=utf-8
# date 2018-01-05 04:53:49
# author calllivecn <c-all@qq.com>

import readline


readline.parse_and_bind('tab: complete')
readline.parse_and_bind('set editing-mode vi')

while True:
	line = input('prompt ("stop" to quit): ')
	if line == 'stop':
		break
	else:
		print('entered:',line)
