#!/usr/bin/env python3 
#coding=utf-8

import os
import time

print('starting....')

print("PPID: {}".format(os.getpid()))

if os.fork():
    for v in range(30):
        print('i am son')
        time.sleep(3)

print('PID: {} done exit'.format(os.getpid()))
