#!/usr/bin/env python3
#coding=utf-8

from evdev import InputDevice
from selectors import DefaultSelector,EVENT_READ
from threading import Thread
import re
import evdev


def __re_true(string):
    if len(re.findall(r'keyboard',string,re.I)) >= 1:
        return True
    else:
        return False

def check_keyboard():
    keyboards = []
    for dev in [ evdev.InputDevice(fn) for fn in evdev.list_devices() ]:
        print(dev.name)
        if __re_true(dev.name):
            print(dev)
            keyboards.append(dev)
    return keyboards


def audio(dev):
    for event in dev.read_loop():
        if event.value == 1 and event.type == 1:
            print('按下键',evdev.ecodes.KEY[event.code],'device:',dev.fn)

def detectInputKey(dev_keyboards):
    while True:
        select([dev], [], [])
        for event in dev.read():
            print("code:{} value:{}".format(event.code, event.value))

if __name__ == '__main__':
    keyboards = check_keyboard()
    selector = DefaultSelector()
    #selector.register(keyboards[0],EVENT_READ)
    #selector.register(keyboards[1],EVENT_READ)
    for kb in keyboards:
        selector.register(kb,EVENT_READ)

    try:
        while True:
            for key, mask in selector.select():
                dev = key.fileobj
                print('有事件发生')
                for event in dev.read():
                    print(event)
                    if event.value == 1 and event.type == 1:
                        pass
                        #print('按下键',evdev.ecodes.KEY[event.code],'device:',dev.fn)

    except KeyboardInterrupt:
        print('\rexit.')
        exit(0)
