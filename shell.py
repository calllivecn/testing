#!/usr/bin/env python3
#coding=utf-8

try:
	import readline
except ImportError:
	print('not found readline library')


import os,sys
from threading import Thread
from selectors import DefaultSelector,EVENT_READ,EVENT_WRITE
from subprocess import Popen,PIPE

CMD='bash'
CMD='./sub.sh'

def getPS1(PS1="SH_PS"):
	ps = os.getenv(PS1)
	if ps:
		return ps
	else:
		return "> "


def getstdout(fd,mask):
	print('getstdout fd , mask',fd,mask)
	print(fd.read().decode())

def getinput(fd,mask):
	print('getinput fd , mask',fd,mask)
	cmd = fd.readline() + '\n'
	if cmd == 'exit'+'\n':
		sp.stdin.write('exit\n'.encode())
		sp.stdin.flush()
		exit(0)
	sp.stdin.write(cmd.encode())
	sp.stdin.flush()


sp = Popen(CMD,stdin=PIPE,shell=True)


#select = DefaultSelector()

#select.register(sys.stdin,EVENT_READ,getinput)
#select.register(sp.stdout,EVENT_READ,getstdout)
#select.register(sp.stderr,EVENT_WRITE,getstdout)
'''
while True:
	events = select.select()
	for key , event in events:
		func = key.data
		func(key.fileobj,event)
'''
def input__():
	cmd=''
	while cmd != 'exit':
		cmd = input("> ")
		cmd2 =  cmd + os.sep
		sp.stdin.write(cmd.encode())
		sp.stdin.flush()

th1 = Thread(target=input__,daemon=True)
th1.start()

try:
	print('subprocess returncode :',sp.wait())
except KeyboardInterrupt:
	pass

#select.close()
