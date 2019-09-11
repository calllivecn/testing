#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-13 18:12:34
# author calllivecn <c-all@qq.com>


import os
import sys
import selectors
#import fcntl

from libevdev import Device, InputEvent

import libkbm


def registers(kbms):
    selector = selectors.DefaultSelector()

    for kbm in kbms:
        print("加入：", kbm)
        fd = os.open(kbm, os.O_NONBLOCK | os.O_RDONLY)
        fdobj = open(fd, "rb")
        #fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        device = Device(fdobj)

        selector.register(device.fd, selectors.EVENT_READ, data=device)

    return selector

s = registers(libkbm.getkbm())

while True:
    print("while 里面")
    for fd, event in s.select():
        print("for select() 里面")
        for e in fd.data.events():
            print("for events() 里面")
            print(e)

"""
成功了～～～
"""

