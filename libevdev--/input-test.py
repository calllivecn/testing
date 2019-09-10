#!/usr/bin/env python3
# coding=utf-8
# date 2019-08-13 18:12:34
# author calllivecn <c-all@qq.com>


import os
import sys
import selectors
import fcntl

from libevdev import Device, InputEvent

import libkbm


#dev_input_event = sys.argv[1]
#dev_input_event2 = sys.argv[2]


def registers(kbms):
    selector = selectors.DefaultSelector()

    for kbm in kbms:
        print("加入：", kbm)
        fd = open(kbm, "rb")
        fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
        device = Device(fd)

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

