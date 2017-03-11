#!/usr/bin/env python3
#coding=utf-8


from evdev import InputDevice,list_devices

'''
dev = InputDevice('/dev/input/event4')

while 1:
	for event in dev.read():
		print('key value',event.code,'up|down',event.value)
'''





#!/usr/bin/env python
#coding: utf-8
from evdev import InputDevice
from select import select

def detectInputKey():
	dev = InputDevice('/dev/input/event4')
	while True:
		select([dev], [], [])
		for event in dev.read():
			print("code:%s value:%s" % (event.code, event.value))



if __name__ == '__main__':
	try:
		detectInputKey()
	except KeyboardInterrupt:
		print('\rexit.')
		exit(1)
