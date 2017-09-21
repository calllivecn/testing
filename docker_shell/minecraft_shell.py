#!/usr/bin/env python3
#coding=utf-8

from threading import Thread
from subprocess import Popen,PIPE
import signal,os


ENV={"MEM_MIN":'',"MEM_MAX":'',"MC_SERVER":''}

for key in ENV.keys():
	ENV[key] = os.getenv(key)

CMD='java -Xms{MEM_MIN}M -Xmx{MEM_MAX}M '\
	'-jar {MC_SERVER}'.format(**ENV)

sub_exit_cmd='exit'

p = Popen(CMD,stdin=PIPE,shell=True)#,universal_newlines=True)
ppid = os.getpid()

print('father pid',ppid)
print('sub pid ',p.pid)

def sig_handler(sig_number,SIG):
	cmd = sub_exit_cmd + os.linesep
	p.stdin.write(cmd.encode())
	p.stdin.flush()

signal.signal(signal.SIGTERM,sig_handler)

cmd = ''
while cmd != sub_exit_cmd:
	cmd = input()
	cmd2 = cmd + os.linesep
	p.stdin.write(cmd2.encode())
	p.stdin.flush()
else:
	cmd = sub_exit_cmd + os.linesep
	p.stdin.write(cmd.encode())
	p.stdin.flush()

print('wait sub end...')

try:
	print('subprocess returncode:',p.wait())
except KeyboardInterrupt:
	sig_handler(1,2)

print('safe exit')

