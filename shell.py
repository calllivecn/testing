#!/usr/bin/env python3
#coding=utf-8

import os,sys
from subprocess import Popen,PIPE

CMD='ping -c 5 -W1 www.baidu.com'
CMD='./sub.sh'
CMD='bash'
CMD='./sub.py'

sp = Popen(CMD,stdin=PIPE,shell=True)

cmd=''
while cmd != 'exit':
	cmd = input(">>>>> ")
	cmd2 = cmd + '\n'
	sp.stdin.write(cmd2.encode())
	sp.stdin.flush()
else:
	sp.stdin.write('exit\n'.encode())
	sp.stdin.flush()

try:
	print('subprocess returncode :',sp.wait())
except KeyboardInterrupt:
	pass

