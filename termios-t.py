#!/usr/bin/env python3
#coding=utf-8

import os,sys,termios,copy

import binascii

try:
	fd = sys.stdin.fileno()
	#print('fd:',fd)
	old_settings = termios.tcgetattr(fd)
	new_settings = copy.deepcopy(old_settings)
	new_settings[3] &= ~(termios.ICANON | termios.ECHO) # | termios.ISIG)
	#new_settings[6][termios.VMIN] = 1
	#new_settings[6][termios.VTIME] = 0
	termios.tcsetattr(fd,termios.TCSADRAIN,new_settings)

	ch = ''
	ESC = 0x1b
	ESC = ESC.to_bytes(1,'big')
	while ch != ESC:
		#ch = sys.stdin.read(8)
		ch = os.read(fd,8)#.decode()
		if ch != ESC:
			os.write(fd,ch)
			#sys.stdout.write('[{}]'.format(ch))
			#sys.stdout.write(ch)
			sys.stdout.flush()

except KeyboardInterrupt:
    pass

finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

