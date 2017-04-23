#!/usr/bin/env python3
#coding=utf-8

import sys,termios,copy



try:
	ch = ''
	fd = sys.stdin.fileno()
	#print('fd:',fd)
	old_settings = termios.tcgetattr(fd)
	new_settings = copy.deepcopy(old_settings)
	new_settings[3] &= ~(termios.ICANON | termios.ECHO) # | termios.ISIG)
	#new_settings[6][termios.VMIN] = 1
	#new_settings[6][termios.VTIME] = 0
	termios.tcsetattr(fd,termios.TCSADRAIN,new_settings)

	while ch != '':
		ch = sys.stdin.read(1)
		sys.stdout.write(ch)
		sys.stdout.flush()

except KeyboardInterrupt:
	pass

finally:
	termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)

