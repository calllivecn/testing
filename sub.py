#!/usr/bin/env python3
#coding=utf-8

import time
from threading import Thread

def randoutput():
	while True:
		print(time.time())
		time.sleep(3)

th = Thread(target=randoutput,daemon=True)
th.start()

cmd=''
while cmd != 'exit':
	cmd = input('sub>>> ')
	print(cmd)



