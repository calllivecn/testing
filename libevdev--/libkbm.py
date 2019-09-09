#!/usr/bin/env python3
# coding=utf-8
# date 2019-09-09 11:43:59
# author calllivecn <c-all@qq.com>


"""
kbm is keyboard mouse
"""

import os
from os import path
from time import sleep

import libevdev as ev
from libevdev import (Device, evbit,)


from logs import logger


def getkbm(baseinput="/dev/input"):
    kbms = []
    
    for dev in os.listdir(baseinput):

        devpath = path.join(baseinput, dev)
        if not path.isdir(devpath):
            devfd = open(devpath, 'rb')

        try:
            device = libevdev.Device(devfd)
        except OSError as e :
            logger.error("打开 {} 异常：{}".format(dev, e))
            continue
    
        #if device.has(EV_REL.REL_X) device.has(EV_REL.REL_Y and device.has(EV_KEY.BTN_LEFT) and device.has(EV_KEY.BTN_RIGHT) and device.has(EV_KEY.BTN_MIDDLE) and device.has(EV_KEY.WHEEL):
        MOUSE = [EV_REL.REL_X, EV_REL.REL_Y, EV_REL.REL_WHEEL ,EV_KEY.BTN_LEFT, EV_KEY.BTN_RIGHT, EV_KEY.BTN_MIDDLE]
    
        KEYBOARD = [EV_KEY.KEY_ESC, EV_KEY.KEY_SPACE, EV_KEY.KEY_BACKSPACE, EV_KEY.KEY_0, EV_KEY.KEY_A, EV_KEY.KEY_Z, EV_KEY.KEY_9, EV_KEY.KEY_F2]
    
        if all(map(device.has, MOUSE)):
            print("应该是鼠标了: ", device.name, "路径：", device.fd)
            kbm.append(dev)
    
        elif all(map(device.has, KEYBOARD)):
            print("应该是键盘了: ", device.name, "路径：", device.fd)
            kbm.append(dev)
    
        #else:
            #print("其他输入设备：", device.name, "路径：",device.fd)
    
        dev.close()
    
    #with open(path.join(baseinput, "event0"), "rb") as fd:
    #    device = libevdev.Device(fd)
    #    print(device.name)


class VirtualKeyboardMouse:
    """
    虚拟键盘鼠标
    """
    def __init__(self):
        self.device = Device()
        self.device.name = "Virtual Keyboard Mouse"
        self.__add_mouse_keyboard_events()
        self.uinput = self.device.create_uinput_device()

        self._sleep = 0.01


    @property
    def sleep(self):
        return self._sleep

    @sleep.setter
    def sleep(self, t):
        if isinstance(t, float) or isinstance(t, int):
            self._sleep = t
        else:
            raise ValueError("t require is int or float.")


    def __add_mouse_keyboard_events(self):
        """
        为虚拟键鼠添加鼠标事件。
        """

        self.device.enable(ev.EV_MSC.MSC_SCAN)

        # 鼠标事件类型
        mouse0 = [ evbit(0, i) for i in range(15) ]
        mouse1 = [ evbit(1, i) for i in range(272, 276+1) ]
        mouse2 = [ evbit(2, 0), evbit(2, 1), evbit(2, 8), evbit(2, 11) ]
        for e in mouse0 + mouse1 + mouse2:
            self.device.enable(e)


        # 键盘事件类型
        keyboard0 = [ evbit(1, i) for i in range(1, 128+1) ]
        for e in keyboard0:
            self.device.enable(e)

        #led = [ evbit(17, 0), evbit(17, 1), evbit(17, 2) ]


    def __key2seq(self, key, downup=1):
        """
        构建事件序列。
        """
        
        if downup == 1 or downup == 0:
            pass
        else:
            raise ValueError("param: downup chioce 1 or 0.")
        

        shiftdown = [ ev.InputEvent(ev.EV_MSC.MSC_SCAN, value=4), 
                    ev.InputEvent(evbit("KEY_LEFTSHIFT"), value=1),
                    ev.InputEvent(ev.EV_SYN.SYN_REPORT, value=0) ]

        shiftup = [ ev.InputEvent(ev.EV_MSC.MSC_SCAN, value=4), 
                    ev.InputEvent(evbit("KEY_LEFTSHIFT"), value=0),
                    ev.InputEvent(ev.EV_SYN.SYN_REPORT, value=0) ]

        key_seq = [ ev.InputEvent(ev.EV_MSC.MSC_SCAN, value=4), 
                    ev.InputEvent(evbit("KEY_" + key.upper()), value=downup),
                    ev.InputEvent(ev.EV_SYN.SYN_REPORT, value=0) ]

        if key.isupper():
            event_seq = shiftdown + key_seq + shiftup
        elif key.islower():
            event_seq = key_seq
        elif key.isdigit():
            event_seq = key_seq

        return event_seq

    def keydown(self, key):
        """
        按下 key.
        """

        self.uinput.send_events(self.__key2seq(key, 1))

    def keyup(self, key):
        """
        松开 key.
        """
        self.uinput.send_events(self.__key2seq(key, 0))

    def key(self, key):
        self.keydown(key)
        sleep(self._sleep)
        self.keyup(key)

    def close(self):
        pass
