#!/usr/bin/env python3
#coding=utf-8


from evdev import InputDevice,list_devices

dev = InputDevice('/dev/input/event4')

while 1:
	for event in dev.read():
		print('key value',event.code,'up|down',event.value)
